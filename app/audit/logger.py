import json
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

from app.db.orm_models import AuditLog
from app.security.sanitizer import sanitize_parameters


def log_audit_event(
    db: Session,
    agent_id: str,
    session_id: str,
    tool: str,
    parameters: Dict[str, Any],
    outcome: str,
    matched_rule: Optional[str],
    status: str,
    latency_ms: float = 0.0,
) -> AuditLog:
    sanitized_parameters = sanitize_parameters(parameters)
    entry = AuditLog(
        timestamp=datetime.now(timezone.utc),
        agent_id=agent_id,
        session_id=session_id,
        tool=tool,
        parameters=json.dumps(sanitized_parameters),
        evaluation_outcome=outcome,
        matched_rule=matched_rule,
        status=status,
        latency_ms=latency_ms,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry
