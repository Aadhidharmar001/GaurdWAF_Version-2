import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.audit.logger import log_audit_event
from app.db.orm_models import HitlQueue
from app.hitl.risk_evaluator import evaluate_hitl_risk
from app.security.sanitizer import sanitize_parameters


def create_hitl_request(
    db: Session,
    agent_id: str,
    session_id: str,
    tool: str,
    parameters: Dict[str, Any],
    matched_rule: Optional[str] = None,
    fraud_score: Optional[float] = None,
    confidence_score: Optional[float] = None,
    risk_level: Optional[str] = None,
    risk_reasons: Optional[List[str]] = None,
) -> HitlQueue:
    sanitized_parameters = sanitize_parameters(parameters)

    if (
        fraud_score is None
        or confidence_score is None
        or risk_level is None
        or risk_reasons is None
    ):
        eval_res = evaluate_hitl_risk(tool, sanitized_parameters, matched_rule)
        fraud_score = eval_res["fraud_score"] if fraud_score is None else fraud_score
        confidence_score = (
            eval_res["confidence_score"]
            if confidence_score is None
            else confidence_score
        )
        risk_level = eval_res["risk_level"] if risk_level is None else risk_level
        risk_reasons = (
            eval_res["risk_reasons"] if risk_reasons is None else risk_reasons
        )

    entry = HitlQueue(
        timestamp=datetime.now(timezone.utc),
        agent_id=agent_id,
        session_id=session_id,
        tool=tool,
        parameters=json.dumps(sanitized_parameters),
        status="pending",
        fraud_score=fraud_score,
        confidence_score=confidence_score,
        risk_level=risk_level,
        risk_reasons=json.dumps(risk_reasons),
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


def get_pending_hitl_requests(db: Session) -> List[Dict[str, Any]]:
    rows = (
        db.query(HitlQueue)
        .filter(HitlQueue.status == "pending")
        .order_by(HitlQueue.id.desc())
        .all()
    )
    results = []
    for r in rows:
        reasons = []
        if r.risk_reasons:
            try:
                reasons = json.loads(r.risk_reasons)
            except Exception:
                reasons = [r.risk_reasons]

        results.append(
            {
                "id": r.id,
                "timestamp": r.timestamp.isoformat(),
                "agent_id": r.agent_id,
                "session_id": r.session_id,
                "tool": r.tool,
                "parameters": json.loads(r.parameters),
                "status": r.status,
                "reason": r.reason,
                "fraud_score": r.fraud_score or 0.0,
                "confidence_score": r.confidence_score or 0.0,
                "risk_level": r.risk_level or "MEDIUM",
                "risk_reasons": reasons,
            }
        )
    return results


def process_hitl_decision(
    db: Session, request_id: int, decision: str, reason: Optional[str] = None
) -> Optional[HitlQueue]:
    entry = db.query(HitlQueue).filter(HitlQueue.id == request_id).first()
    if not entry:
        return None

    status = "approved" if decision == "approve" else "rejected"
    entry.status = status
    entry.reason = reason
    db.commit()

    params = json.loads(entry.parameters)
    log_audit_event(
        db=db,
        agent_id=entry.agent_id,
        session_id=entry.session_id,
        tool=entry.tool,
        parameters=params,
        outcome=f"HITL Decision: {status.upper()}. Reason: {reason or 'None'}",
        matched_rule="HITL Override",
        status="allowed" if status == "approved" else "blocked",
    )
    return entry
