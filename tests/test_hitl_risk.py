import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.orm_models import Base
from app.hitl.queue_manager import create_hitl_request, get_pending_hitl_requests
from app.hitl.risk_evaluator import evaluate_hitl_risk


@pytest.fixture
def db_session():
    engine = create_engine(
        "sqlite:///:memory:", connect_args={"check_same_thread": False}
    )
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


def test_evaluate_hitl_risk_external_email():
    res = evaluate_hitl_risk(
        "send_email", {"recipient": "attacker@external.com", "subject": "Data Leak"}
    )
    assert res["fraud_score"] >= 80.0
    assert res["confidence_score"] >= 90.0
    assert res["risk_level"] in ["HIGH", "CRITICAL"]
    assert any("External recipient" in reason for reason in res["risk_reasons"])


def test_evaluate_hitl_risk_internal_email():
    res = evaluate_hitl_risk(
        "send_email", {"recipient": "employee@aivar.com", "subject": "Meeting"}
    )
    assert res["fraud_score"] < 50.0
    assert res["risk_level"] in ["LOW", "MEDIUM"]


def test_evaluate_hitl_risk_sql_injection():
    res = evaluate_hitl_risk(
        "execute_query", {"query": "SELECT * FROM users; DROP TABLE users;"}
    )
    assert res["fraud_score"] >= 85.0
    assert res["risk_level"] == "CRITICAL"
    assert any("SQL pattern" in reason for reason in res["risk_reasons"])


def test_create_and_get_pending_hitl_requests(db_session):
    entry = create_hitl_request(
        db=db_session,
        agent_id="test-agent",
        session_id="session-risk-1",
        tool="send_email",
        parameters={"recipient": "exfiltrate@outside.org"},
    )
    assert entry.id is not None
    assert entry.fraud_score > 0.0
    assert entry.confidence_score > 0.0
    assert entry.risk_level is not None

    pending = get_pending_hitl_requests(db_session)
    assert len(pending) == 1
    req = pending[0]
    assert req["fraud_score"] == entry.fraud_score
    assert req["confidence_score"] == entry.confidence_score
    assert req["risk_level"] == entry.risk_level
    assert isinstance(req["risk_reasons"], list)
