"""
Comprehensive Test Suite for Phase 2 Resumable HITL Workflows & State Machine Transitions.
"""

from datetime import datetime, timedelta, timezone

import pytest

from guardwaf import (
    ActionState,
    GuardWAF,
    GuardWAFActionExpiredError,
    GuardWAFAlreadyExecutedError,
    GuardWAFHITLRequiredError,
    GuardWAFInvalidStateTransitionError,
    GuardWAFSecurityError,
    protect,
    session,
)


@pytest.fixture
def waf_client():
    return GuardWAF(config_path="rules.yaml")


# --- Test 1: Approved action resumes correctly ---
@pytest.mark.asyncio
async def test_approved_action_resumes_correctly(waf_client):
    side_effect = False

    @protect(tool_name="lookup_customer")
    def lookup_customer(customer_id: str):
        return {"status": "found"}

    @protect(tool_name="process_refund")
    def process_refund(customer_id: str, amount: float):
        nonlocal side_effect
        side_effect = True
        return {"status": "SUCCESS", "refunded": amount}

    with session(session_id="sess_res_01", customer_id="cust_alice"):
        lookup_customer("cust_alice")

        pending_id = None
        appr_token = None

        # 1. Trigger HITL Exception
        try:
            process_refund("cust_alice", 250.0)
        except GuardWAFHITLRequiredError as e:
            pending_id = e.pending_action_id
            appr_token = e.approval_token

        assert pending_id is not None
        assert side_effect is False  # Function body not executed yet!

        # 2. Human Approves Action
        pending_act = waf_client.approve_pending_action(
            pending_id, approver_id="security_admin"
        )
        assert pending_act.status == ActionState.APPROVED
        assert pending_act.approval_token is not None

        # 3. Resume Execution
        result = await waf_client.resume(pending_id, pending_act.approval_token)
        assert result["status"] == "SUCCESS"
        assert result["refunded"] == 250.0
        assert side_effect is True  # Function body executed exactly once!

        # 4. Verify Final State is EXECUTED
        final_action = waf_client.state_store.get_pending_action(pending_id)
        assert final_action.status == ActionState.EXECUTED
        assert final_action.execution_status == "EXECUTED"


# --- Test 2: Denied action never executes ---
@pytest.mark.asyncio
async def test_denied_action_never_executes(waf_client):
    executed = False

    @protect(tool_name="lookup_customer")
    def lookup_customer(customer_id: str):
        return {"status": "found"}

    @protect(tool_name="process_refund")
    def process_refund(customer_id: str, amount: float):
        nonlocal executed
        executed = True
        return {"status": "SUCCESS"}

    with session(session_id="sess_deny_01", customer_id="cust_bob"):
        lookup_customer("cust_bob")
        try:
            process_refund("cust_bob", 300.0)
        except GuardWAFHITLRequiredError as e:
            pending_id = e.pending_action_id

        # Human Denies Action
        waf_client.deny_pending_action(
            pending_id, approver_id="security_admin", reason="Over spending limit"
        )

        # Resume attempt MUST fail
        with pytest.raises(GuardWAFSecurityError) as exc:
            await waf_client.resume(pending_id, "dummy_token")

        assert "DENIED" in str(exc.value)
        assert executed is False


# --- Test 3: Expired action never executes ---
@pytest.mark.asyncio
async def test_expired_action_never_executes(waf_client):
    @protect(tool_name="lookup_customer")
    def lookup_customer(customer_id: str):
        return {"status": "found"}

    @protect(tool_name="process_refund")
    def process_refund(customer_id: str, amount: float):
        return {"status": "SUCCESS"}

    with session(session_id="sess_exp_01", customer_id="cust_exp"):
        lookup_customer("cust_exp")
        try:
            process_refund("cust_exp", 400.0)
        except GuardWAFHITLRequiredError as e:
            pending_id = e.pending_action_id

        # Manually force expiration in state store
        action = waf_client.state_store.get_pending_action(pending_id)
        action.expires_at = datetime.now(timezone.utc) - timedelta(seconds=10)
        waf_client.state_store.save_pending_action(action)

        # Attempt to approve expired action -> Fails
        with pytest.raises(GuardWAFActionExpiredError):
            waf_client.approve_pending_action(pending_id)

        # Resume attempt -> Fails
        with pytest.raises(GuardWAFActionExpiredError):
            await waf_client.resume(pending_id, "dummy_token")


# --- Test 4: Replaying an already executed action fails ---
@pytest.mark.asyncio
async def test_replay_approval_fails(waf_client):
    @protect(tool_name="lookup_customer")
    def lookup_customer(customer_id: str):
        return {"status": "found"}

    @protect(tool_name="process_refund")
    def process_refund(customer_id: str, amount: float):
        return {"status": "SUCCESS"}

    with session(session_id="sess_replay_01", customer_id="cust_replay"):
        lookup_customer("cust_replay")
        try:
            process_refund("cust_replay", 150.0)
        except GuardWAFHITLRequiredError as e:
            pending_id = e.pending_action_id

        appr_act = waf_client.approve_pending_action(pending_id)

        # First Resume succeeds
        res1 = await waf_client.resume(pending_id, appr_act.approval_token)
        assert res1["status"] == "SUCCESS"

        # Second Resume (REPLAY ATTEMPT) MUST FAIL
        with pytest.raises(GuardWAFAlreadyExecutedError):
            await waf_client.resume(pending_id, appr_act.approval_token)


# --- Test 5: Parameter tampering invalidates grant ---
@pytest.mark.asyncio
async def test_modified_parameters_fail_verification(waf_client):
    @protect(tool_name="lookup_customer")
    def lookup_customer(customer_id: str):
        return {"status": "found"}

    @protect(tool_name="process_refund")
    def process_refund(customer_id: str, amount: float):
        return {"status": "SUCCESS"}

    with session(session_id="sess_tamper_01", customer_id="cust_tamper"):
        lookup_customer("cust_tamper")
        try:
            process_refund("cust_tamper", 200.0)
        except GuardWAFHITLRequiredError as e:
            pending_id = e.pending_action_id

        appr_act = waf_client.approve_pending_action(pending_id)

        # Tamper with stored parameters in state store (e.g. change 200 to 20000)
        tampered_act = waf_client.state_store.get_pending_action(pending_id)
        tampered_act.parameters = {"customer_id": "cust_tamper", "amount": 20000.0}
        waf_client.state_store.save_pending_action(tampered_act)

        # Resume attempt -> Digest Mismatch Fails
        with pytest.raises(GuardWAFSecurityError) as exc:
            await waf_client.resume(pending_id, appr_act.approval_token)

        assert "digest mismatch" in str(exc.value).lower()


# --- Test 6: Wrong session cannot resume action ---
@pytest.mark.asyncio
async def test_wrong_session_cannot_resume_action(waf_client):
    @protect(tool_name="lookup_customer")
    def lookup_customer(customer_id: str):
        return {"status": "found"}

    @protect(tool_name="process_refund")
    def process_refund(customer_id: str, amount: float):
        return {"status": "SUCCESS"}

    with session(session_id="sess_correct", customer_id="cust_orig"):
        lookup_customer("cust_orig")
        try:
            process_refund("cust_orig", 180.0)
        except GuardWAFHITLRequiredError as e:
            pending_id = e.pending_action_id

    appr_act = waf_client.approve_pending_action(pending_id)

    # Attempt to resume from Session 2 (Attacker Session)
    with session(session_id="sess_attacker", customer_id="cust_attacker"):
        with pytest.raises(GuardWAFSecurityError) as exc:
            await waf_client.resume(pending_id, appr_act.approval_token)
        assert "session mismatch" in str(exc.value).lower()


# --- Test 7: Invalid state machine transition rejected ---
def test_invalid_state_transitions(waf_client):
    @protect(tool_name="lookup_customer")
    def lookup_customer(customer_id: str):
        return {"status": "found"}

    @protect(tool_name="process_refund")
    def process_refund(customer_id: str, amount: float):
        return {"status": "SUCCESS"}

    with session(session_id="sess_trans_01", customer_id="cust_tr"):
        lookup_customer("cust_tr")
        try:
            process_refund("cust_tr", 350.0)
        except GuardWAFHITLRequiredError as e:
            pending_id = e.pending_action_id

    # PENDING -> DENIED
    waf_client.deny_pending_action(pending_id)

    # DENIED -> APPROVED (Invalid transition) MUST fail
    with pytest.raises(GuardWAFInvalidStateTransitionError):
        waf_client.approve_pending_action(pending_id)
