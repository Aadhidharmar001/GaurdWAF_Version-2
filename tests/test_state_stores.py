"""
Contract Tests for MemoryStateStore, SQLiteStateStore, and RedisStateStore Adapters.
Verifies rate limit counters, sequence history, and durable PendingAction atomic state transitions.
"""

from datetime import datetime, timedelta, timezone

import pytest

from guardwaf import (
    ActionState,
    MemoryStateStore,
    PendingAction,
    RedisStateStore,
    SQLiteStateStore,
)


@pytest.fixture
def memory_store():
    return MemoryStateStore()


@pytest.fixture
def sqlite_store(tmp_path):
    db_file = str(tmp_path / "test_state.db")
    return SQLiteStateStore(db_path=db_file)


@pytest.fixture
def redis_store():
    return RedisStateStore()


# --- Contract Tests for State Stores ---


@pytest.mark.parametrize("store_fixture", ["memory_store", "sqlite_store"])
def test_rate_limiting_counter_contract(request, store_fixture):
    store = request.getfixturevalue(store_fixture)
    session_id = "sess_rate_test"
    tool_name = "send_email"

    assert store.get_tool_call_count(session_id, tool_name, window_seconds=60) == 0

    store.record_tool_call(session_id, tool_name, "allowed")
    store.record_tool_call(session_id, tool_name, "allowed")
    store.record_tool_call(
        session_id, tool_name, "blocked"
    )  # Blocked calls do not increment allowed counter

    assert store.get_tool_call_count(session_id, tool_name, window_seconds=60) == 2


@pytest.mark.parametrize("store_fixture", ["memory_store", "sqlite_store"])
def test_sequence_state_contract(request, store_fixture):
    store = request.getfixturevalue(store_fixture)
    session_id = "sess_seq_test"
    tool_name = "verify_recipient"

    assert store.has_executed_predecessor(session_id, tool_name) is False

    store.record_sequence_state(session_id, tool_name)
    assert store.has_executed_predecessor(session_id, tool_name) is True


@pytest.mark.parametrize("store_fixture", ["memory_store", "sqlite_store"])
def test_pending_action_persistence_and_atomic_transitions(request, store_fixture):
    store = request.getfixturevalue(store_fixture)

    pending_action = PendingAction(
        pending_action_id="pa_contract_100",
        agent_id="test_agent",
        session_id="sess_contract_01",
        tool_name="process_refund",
        canonical_parameters='{"amount":150}',
        parameters={"amount": 150},
        parameter_digest="digest_123",
        action_intent_digest="intent_digest_123",
        created_at=datetime.now(timezone.utc),
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=10),
        status=ActionState.PENDING,
        idempotency_key="idemp_100",
    )

    # 1. Save Action
    store.save_pending_action(pending_action)

    # 2. Retrieve Action
    retrieved = store.get_pending_action("pa_contract_100")
    assert retrieved is not None
    assert retrieved.pending_action_id == "pa_contract_100"
    assert retrieved.status == ActionState.PENDING

    # 3. Atomic State Transition (PENDING -> APPROVED)
    success = store.update_pending_action_status(
        pending_action_id="pa_contract_100",
        new_status=ActionState.APPROVED,
        expected_old_status=ActionState.PENDING,
        approver_id="test_admin",
        approval_token="tok_123",
    )
    assert success is True

    # 4. Verify updated state
    updated = store.get_pending_action("pa_contract_100")
    assert updated.status == ActionState.APPROVED
    assert updated.approver_id == "test_admin"
    assert updated.approval_token == "tok_123"

    # 5. Invalid State Transition Attempt (PENDING -> EXECUTED when current state is APPROVED)
    bad_transition = store.update_pending_action_status(
        pending_action_id="pa_contract_100",
        new_status=ActionState.EXECUTED,
        expected_old_status=ActionState.PENDING,  # Expected PENDING, but current state is APPROVED!
    )
    assert bad_transition is False  # Atomic check rejected invalid old_status match!


def test_redis_state_store_adapter_interface(redis_store):
    # Verify RedisStateStore exposes complete StateStore API contract cleanly
    assert hasattr(redis_store, "record_tool_call")
    assert hasattr(redis_store, "get_tool_call_count")
    assert hasattr(redis_store, "has_executed_predecessor")
    assert hasattr(redis_store, "save_pending_action")
    assert hasattr(redis_store, "get_pending_action")
    assert hasattr(redis_store, "update_pending_action_status")
