from app.models import RuleResult

def apply_shadow_mode_transformation(result: RuleResult) -> RuleResult:
    """
    If a rule result is shadow_blocked, transform its disposition so that the agent call
    is allowed to execute, but the audit log records the rule violation as shadow_blocked.
    """
    if result.status == "shadow_blocked":
        return RuleResult(
            status="allowed",
            outcome=f"[SHADOW MODE] Violation detected: {result.outcome}. Action allowed in shadow mode.",
            matched_rule=f"[SHADOW] {result.matched_rule}"
        )
    return result
