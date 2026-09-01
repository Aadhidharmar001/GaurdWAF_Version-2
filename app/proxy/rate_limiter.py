from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy.orm import Session

from app.db.orm_models import AuditLog
from app.models import RateLimitRule, RuleResult, ToolCallRequest


def evaluate_rate_limit(
    req: ToolCallRequest, rule: RateLimitRule, db: Session, global_shadow: bool = False
) -> Optional[RuleResult]:
    if rule.tool != req.tool:
        return None

    one_minute_ago = datetime.now(timezone.utc) - timedelta(seconds=60)
    count = (
        db.query(AuditLog)
        .filter(
            AuditLog.tool == req.tool,
            AuditLog.session_id == req.session_id,
            AuditLog.timestamp >= one_minute_ago,
            AuditLog.status.in_(["allowed", "shadow_blocked"]),
        )
        .count()
    )

    if count >= rule.max_calls_per_minute:
        is_shadow = rule.shadow_mode or global_shadow
        status = "shadow_blocked" if is_shadow else "blocked"
        return RuleResult(
            status=status,
            outcome=f"Rate limit exceeded: Max {rule.max_calls_per_minute} calls/min for tool '{req.tool}' (Current: {count})",
            matched_rule=f"rate_limits: max {rule.max_calls_per_minute}/min",
        )
    return None
