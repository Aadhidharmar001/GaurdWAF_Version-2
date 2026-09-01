from typing import Optional

from sqlalchemy.orm import Session

from app.db.orm_models import SequenceState
from app.models import RuleResult, SequenceRule, ToolCallRequest


def evaluate_sequence(
    req: ToolCallRequest, rule: SequenceRule, db: Session, global_shadow: bool = False
) -> Optional[RuleResult]:
    if rule.tool != req.tool:
        return None

    # Query persistent DB for required predecessor tool in this session
    record = (
        db.query(SequenceState)
        .filter(
            SequenceState.session_id == req.session_id,
            SequenceState.tool_name == rule.required_predecessor,
        )
        .first()
    )

    if not record:
        is_shadow = rule.shadow_mode or global_shadow
        status = "shadow_blocked" if is_shadow else "blocked"
        return RuleResult(
            status=status,
            outcome=f"Sequence Violation: Tool '{req.tool}' requires prior execution of '{rule.required_predecessor}' in session '{req.session_id}'",
            matched_rule=f"sequences: required '{rule.required_predecessor}'",
        )
    return None


def record_sequence_state(session_id: str, tool_name: str, db: Session):
    state = SequenceState(session_id=session_id, tool_name=tool_name)
    db.add(state)
    db.commit()
