"""
Comprehensive Unit Test Suite for GuardWAF Python SDK & In-Process Execution Interceptor.
Validates deterministic execution blocking, context isolation, canonical parameter hashing, sequence guards, rate limits, and async support.
"""

import asyncio

import pytest

from guardwaf import GuardWAF, protect, session
from guardwaf.core.canonical import compute_parameter_digest
from guardwaf.core.models import ActionIntent, SessionContext
from guardwaf.exceptions import GuardWAFHITLRequiredError, GuardWAFSecurityError


@pytest.fixture(autouse=True)
def init_guardwaf_client():
    # Initialize GuardWAF with rules.yaml
    client = GuardWAF(config_path="rules.yaml")
    return client


# --- Test 1: Blocked action does NOT execute function body ---
def test_blocked_action_does_not_execute_body(init_guardwaf_client):
    side_effect_executed = False

    @protect(tool_name="process_refund")
    def dangerous_refund(customer_id: str, amount: float):
        nonlocal side_effect_executed
        side_effect_executed = True
        return {"refunded": amount}

    # Sequence required: lookup_customer must run first
    with pytest.raises(GuardWAFSecurityError) as exc_info:
        dangerous_refund("cust_123", 50.0)

    # PROOF: Function body NEVER executed!
    assert side_effect_executed is False
    assert "Sequence Violation" in str(exc_info.value)


# --- Test 2: Valid action executes ---
def test_valid_action_executes(init_guardwaf_client):
    @protect(tool_name="lookup_customer")
    def lookup_customer(customer_id: str):
        return {"status": "found", "customer_id": customer_id}

    with session(session_id="sess_valid_01", customer_id="cust_100"):
        res = lookup_customer("cust_100")
        assert res["status"] == "found"
        assert res["customer_id"] == "cust_100"


# --- Test 3 & 4: Sequence enforcement & correct sequence ---
def test_sequence_enforcement(init_guardwaf_client):
    @protect(tool_name="lookup_customer")
    def lookup_customer(customer_id: str):
        return {"status": "active"}

    @protect(tool_name="process_refund")
    def process_refund(customer_id: str, amount: float):
        return {"success": True}

    with session(session_id="sess_seq_01", customer_id="cust_100"):
        # 1. Attempt refund directly -> Blocked
        with pytest.raises(GuardWAFSecurityError):
            process_refund("cust_100", 50.0)

        # 2. Run required predecessor
        lookup_customer("cust_100")

        # 3. Attempt refund again -> Allowed
        res = process_refund("cust_100", 50.0)
        assert res["success"] is True


# --- Test 5: Data scope mismatch blocks ---
def test_data_scope_mismatch_blocks(init_guardwaf_client):
    @protect(tool_name="lookup_customer")
    def lookup_customer(customer_id: str):
        return {"status": "active"}

    @protect(tool_name="process_refund")
    def process_refund(customer_id: str, amount: float):
        return {"success": True}

    with session(session_id="sess_scope_01", customer_id="cust_A"):
        lookup_customer("cust_A")
        # Attempt refund for cust_B while session is cust_A -> Blocked
        with pytest.raises(GuardWAFSecurityError) as exc:
            process_refund("cust_B", 50.0)
        assert "Data Scope Mismatch" in str(exc.value)


# --- Test 6: Rate limit blocks ---
def test_rate_limit_blocks(init_guardwaf_client):
    @protect(tool_name="lookup_customer")
    def lookup_customer(customer_id: str):
        return {"status": "active"}

    @protect(tool_name="process_refund")
    def process_refund(customer_id: str, amount: float):
        return {"success": True}

    with session(session_id="sess_rate_01", customer_id="cust_100"):
        lookup_customer("cust_100")
        # Rule max 3 calls/min
        process_refund("cust_100", 10.0)
        process_refund("cust_100", 10.0)
        process_refund("cust_100", 10.0)

        # 4th call -> Rate Limit Exceeded Blocked
        with pytest.raises(GuardWAFSecurityError) as exc:
            process_refund("cust_100", 10.0)
        assert "Rate Limit Exceeded" in str(exc.value)


# --- Test 7: Separate sessions maintain separate sequence history ---
def test_separate_sessions_sequence_isolation(init_guardwaf_client):
    @protect(tool_name="lookup_customer")
    def lookup_customer(customer_id: str):
        return {"status": "active"}

    @protect(tool_name="process_refund")
    def process_refund(customer_id: str, amount: float):
        return {"success": True}

    # Session 1 runs lookup
    with session(session_id="sess_iso_01", customer_id="cust_1"):
        lookup_customer("cust_1")

    # Session 2 attempts refund without lookup -> MUST be blocked
    with session(session_id="sess_iso_02", customer_id="cust_2"):
        with pytest.raises(GuardWAFSecurityError):
            process_refund("cust_2", 50.0)


# --- Test 8: Context isolation across execution scopes ---
def test_context_isolation():
    with session(session_id="sess_alpha", customer_id="cust_alpha"):
        s1 = session
        from guardwaf.sdk.context import get_current_session

        assert get_current_session().customer_id == "cust_alpha"

    assert get_current_session() is None


# --- Test 9: Parameter digest is deterministic ---
def test_canonical_parameter_digest():
    p1 = {"b": 2, "a": 1, "c": [3, 2, 1]}
    p2 = {"a": 1, "c": [3, 2, 1], "b": 2}

    d1 = compute_parameter_digest(p1)
    d2 = compute_parameter_digest(p2)
    assert d1 == d2


# --- Test 10: Grant signature verification ---
def test_grant_signature_verification(init_guardwaf_client):
    intent = ActionIntent(
        intent_id="int_01",
        agent_id="agent_01",
        tool_name="test_tool",
        parameters={"amount": 50},
        parameter_digest=compute_parameter_digest({"amount": 50}),
        session_context=SessionContext(session_id="sess_grant"),
    )
    grant = init_guardwaf_client.signer.issue_grant(intent)
    assert (
        init_guardwaf_client.signer.verify_grant(grant, intent.parameter_digest) is True
    )

    # Mutated digest fails verification
    assert (
        init_guardwaf_client.signer.verify_grant(grant, "mutated_digest_123") is False
    )


# --- Test 11: Async protected function enforcement ---
@pytest.mark.asyncio
async def test_async_protected_function(init_guardwaf_client):
    side_effect = False

    @protect(tool_name="lookup_customer")
    async def async_lookup(customer_id: str):
        nonlocal side_effect
        await asyncio.sleep(0.01)
        side_effect = True
        return {"status": "ok"}

    with session(session_id="sess_async", customer_id="cust_async"):
        res = await async_lookup("cust_async")
        assert res["status"] == "ok"
        assert side_effect is True


# --- Test 12: HITL required produces pending exception ---
def test_hitl_required_exception(init_guardwaf_client):
    @protect(tool_name="lookup_customer")
    def lookup_customer(customer_id: str):
        return {"status": "active"}

    @protect(tool_name="process_refund")
    def process_refund(customer_id: str, amount: float):
        return {"success": True}

    with session(session_id="sess_hitl_01", customer_id="cust_hitl"):
        lookup_customer("cust_hitl")
        # Amount > 100 triggers HITL rule in rules.yaml
        with pytest.raises(GuardWAFHITLRequiredError) as exc_info:
            process_refund("cust_hitl", 250.0)

        assert exc_info.value.hitl_id.startswith(("hitl_", "pa_"))
        assert exc_info.value.approval_token is not None
