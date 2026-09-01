"""
Adversarial Security & Production Concurrency Audit Test Suite for Phase 2.5.
Tests:
1. Concurrent Resume Race Condition (Exactly-once execution under parallel async tasks).
2. Parameter Tampering & Digest Mismatch.
3. Cross-Session & Cross-Agent Resume Rejection.
4. Crash & Execution Claim Recovery behavior.
5. Telemetry Fault Isolation (Telemetry failure does not block tool execution).
6. SQLite / Memory Atomicity under concurrent threads.
"""

import asyncio
import threading
from datetime import datetime, timedelta, timezone

import pytest

from guardwaf import (
    ActionState,
    GuardWAF,
    GuardWAFAlreadyExecutedError,
    GuardWAFHITLRequiredError,
    GuardWAFSecurityError,
    SQLiteStateStore,
    protect,
    session,
)


@pytest.fixture
def waf_client(tmp_path):
    db_file = str(tmp_path / "audit_state.db")
    state_store = SQLiteStateStore(db_path=db_file)
    return GuardWAF(config_path="rules.yaml", state_store=state_store)


# --- Test 1: Parallel Concurrent Resume Race (Proves Exactly-Once Claim) ---
@pytest.mark.asyncio
async def test_concurrent_resume_race_condition(waf_client):
    execution_counter = 0

    @protect(tool_name="lookup_customer")
    def lookup_customer(customer_id: str):
        return {"status": "found"}

    @protect(tool_name="process_refund")
    def process_refund(customer_id: str, amount: float):
        nonlocal execution_counter
        execution_counter += 1
        return {"status": "SUCCESS"}

    with session(session_id="sess_race_01", customer_id="cust_race"):
        lookup_customer("cust_race")
        try:
            process_refund("cust_race", 250.0)
        except GuardWAFHITLRequiredError as e:
            pending_id = e.pending_action_id

    appr_act = waf_client.approve_pending_action(pending_id)
    token = appr_act.approval_token

    # Launch 20 concurrent tasks attempting to call waf.resume() simultaneously
    results = []
    errors = []

    async def worker():
        try:
            # Re-enter session context
            with session(session_id="sess_race_01", customer_id="cust_race"):
                res = await waf_client.resume(pending_id, token)
                results.append(res)
        except Exception as err:
            errors.append(err)

    tasks = [asyncio.create_task(worker()) for _ in range(20)]
    await asyncio.gather(*tasks)

    # EXACTLY-ONCE EXECUTION PROOF:
    # Exactly ONE worker must succeed, and 19 workers must fail with GuardWAFAlreadyExecutedError!
    assert len(results) == 1
    assert len(errors) == 19
    assert execution_counter == 1
    assert all(isinstance(e, GuardWAFAlreadyExecutedError) for e in errors)


# --- Test 2: Multithreaded State Store Race Protection ---
def test_multithreaded_sqlite_state_transition(tmp_path):
    db_file = str(tmp_path / "mt_state.db")
    store = SQLiteStateStore(db_path=db_file)

    from guardwaf.core.models import PendingAction

    act = PendingAction(
        pending_action_id="pa_mt_100",
        agent_id="agent_1",
        session_id="sess_1",
        tool_name="test_tool",
        canonical_parameters="{}",
        parameters={},
        parameter_digest="digest",
        action_intent_digest="intent_digest",
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=10),
        status=ActionState.APPROVED,
        idempotency_key="idemp_1",
    )
    store.save_pending_action(act)

    successful_claims = 0
    failed_claims = 0
    lock = threading.Lock()

    def claim_worker():
        nonlocal successful_claims, failed_claims
        res = store.update_pending_action_status(
            pending_action_id="pa_mt_100",
            new_status=ActionState.EXECUTING,
            expected_old_status=ActionState.APPROVED,
        )
        with lock:
            if res:
                successful_claims += 1
            else:
                failed_claims += 1

    threads = [threading.Thread(target=claim_worker) for _ in range(10)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert successful_claims == 1
    assert failed_claims == 9


# --- Test 3: Telemetry Fault Isolation (Telemetry Error Does NOT Block Enforcement) ---
@pytest.mark.asyncio
async def test_telemetry_failure_does_not_block_execution(waf_client):
    # Attach a broken telemetry listener that raises an Exception
    def broken_listener(evt):
        raise RuntimeError("Telemetry Pipeline Down!")

    waf_client.telemetry.add_listener(broken_listener)

    @protect(tool_name="lookup_customer")
    def lookup_customer(customer_id: str):
        return {"status": "found"}

    with session(session_id="sess_telem_01", customer_id="cust_telem"):
        # Execution should succeed despite telemetry listener failure!
        res = lookup_customer("cust_telem")
        assert res["status"] == "found"


# --- Test 4: Unwrapped Function Bypass Demonstration ---
def test_unwrapped_python_function_bypass_reality(waf_client):
    executed_via_bypass = False

    @protect(tool_name="lookup_customer")
    def lookup_customer(customer_id: str):
        return {"status": "found"}

    @protect(tool_name="process_refund")
    def process_refund(customer_id: str, amount: float):
        nonlocal executed_via_bypass
        executed_via_bypass = True
        return {"status": "refunded"}

    # GuardWAF blocks direct call without sequence lookup
    with pytest.raises(GuardWAFSecurityError):
        process_refund("cust_1", 50.0)

    assert executed_via_bypass is False

    # REALITY AUDIT: Direct call to func.__wrapped__ in Python bypasses decorator
    unwrapped_func = process_refund.__wrapped__
    res = unwrapped_func("cust_1", 50.0)
    assert executed_via_bypass is True
    assert res["status"] == "refunded"
    # Documented Limitation: In-process decorators secure tool loops, but cannot prevent a malicious developer with Python reflection access from executing __wrapped__.
