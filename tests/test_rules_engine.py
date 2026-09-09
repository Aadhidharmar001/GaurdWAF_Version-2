import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.audit.logger import log_audit_event
from app.db.orm_models import AuditLog, Base
from app.hitl.queue_manager import create_hitl_request
from app.models import PolicyConfig, SessionContext, ToolCallRequest
from app.proxy.interceptor import evaluate_tool_call_request
from app.proxy.sequence_guard import record_sequence_state
from app.rules_engine.loader import load_policy_from_yaml


@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


@pytest.fixture
def policy():
    return load_policy_from_yaml("rules.yaml")


def test_rate_limiting(db_session, policy):
    req = ToolCallRequest(
        agent_id="test-agent",
        session_id="session-rate-1",
        tool="send_email",
        parameters={"recipient": "test@aivar.com"},
    )
    for _ in range(3):
        log_audit_event(
            db_session,
            req.agent_id,
            req.session_id,
            req.tool,
            req.parameters,
            "Clear",
            None,
            "allowed",
        )

    result = evaluate_tool_call_request(req, policy, db_session)
    assert result.status == "blocked"
    assert "Rate limit exceeded" in result.outcome


def test_parameter_blocklist(db_session, policy):
    req = ToolCallRequest(
        agent_id="test-agent",
        session_id="session-param-1",
        tool="execute_query",
        parameters={"query": "SELECT * FROM users; DROP TABLE users;"},
    )
    result = evaluate_tool_call_request(req, policy, db_session)
    assert result.status == "blocked"
    assert "drop table" in result.outcome.lower()


def test_session_aware_data_scope_mismatch(db_session, policy):
    req = ToolCallRequest(
        agent_id="test-agent",
        session_id="session-scope-1",
        tool="delete_records",
        parameters={"record_count": 10, "customer_id": "CUST-999"},
        session_context=SessionContext(customer_id="CUST-100"),
    )
    result = evaluate_tool_call_request(req, policy, db_session)
    assert result.status == "blocked"
    assert "Data Scope Mismatch" in result.outcome


def test_declared_scope_allow_list_blocks_out_of_scope_access(db_session, policy):
    req = ToolCallRequest(
        agent_id="test-agent",
        session_id="session-scope-2",
        tool="delete_records",
        parameters={"record_count": 5, "customer_id": "CUST-300"},
        session_context=SessionContext(allowed_scope_ids=["CUST-100", "CUST-200"]),
    )
    result = evaluate_tool_call_request(req, policy, db_session)
    assert result.status == "blocked"
    assert "Declared Scope Violation" in result.outcome


def test_stateful_sequence_enforcement(db_session, policy):
    session_id = "session-seq-1"
    req_email = ToolCallRequest(
        agent_id="test-agent",
        session_id=session_id,
        tool="send_email",
        parameters={"recipient": "user@aivar.com"},
    )

    res1 = evaluate_tool_call_request(req_email, policy, db_session)
    assert res1.status == "blocked"
    assert "Sequence Violation" in res1.outcome

    record_sequence_state(session_id, "verify_recipient", db_session)

    res2 = evaluate_tool_call_request(req_email, policy, db_session)
    assert res2.status == "allowed"


def test_structured_audit_logging(db_session):
    params = {"query": "SELECT 1;"}
    entry = log_audit_event(
        db=db_session,
        agent_id="agent-007",
        session_id="session-audit-1",
        tool="execute_query",
        parameters=params,
        outcome="Clear",
        matched_rule="test_rule",
        status="allowed",
    )

    logged = db_session.query(AuditLog).filter_by(id=entry.id).first()
    assert logged is not None
    assert logged.agent_id == "agent-007"
    assert logged.session_id == "session-audit-1"
    assert logged.tool == "execute_query"
    assert logged.matched_rule == "test_rule"
    assert logged.status == "allowed"


def test_audit_logging_sanitizes_parameters(db_session):
    raw_params = {
        "query": "SELECT * FROM audit_table " + ("x" * 400),
        "api_key": "super-secret-value",
    }
    entry = log_audit_event(
        db=db_session,
        agent_id="agent-redact",
        session_id="session-redact-1",
        tool="execute_query",
        parameters=raw_params,
        outcome="Clear",
        matched_rule=None,
        status="allowed",
    )

    logged = db_session.query(AuditLog).filter_by(id=entry.id).first()
    assert "[REDACTED]" in logged.parameters
    assert "[truncated]" in logged.parameters


def test_hitl_queue_sanitizes_parameters(db_session):
    entry = create_hitl_request(
        db_session,
        "agent-hitl",
        "session-hitl",
        "send_email",
        {"body": "safe", "token": "secret-token"},
    )
    assert entry is not None
    assert "secret-token" not in entry.parameters


def test_shadow_mode(db_session, policy):
    shadow_policy = PolicyConfig.model_validate(policy.model_dump())
    shadow_policy.shadow_mode = True

    req = ToolCallRequest(
        agent_id="test-agent",
        session_id="session-shadow-1",
        tool="execute_query",
        parameters={"query": "DROP TABLE test;"},
    )

    result = evaluate_tool_call_request(req, shadow_policy, db_session)
    assert result.status == "allowed"
    assert "[SHADOW MODE]" in result.outcome
