from typing import Optional

from app.models import (
    BulkThresholdRule,
    ParameterBlocklistRule,
    RuleResult,
    ToolCallRequest,
)


def evaluate_bulk_threshold(req: ToolCallRequest, rule: BulkThresholdRule, global_shadow: bool = False) -> Optional[RuleResult]:
    if rule.tool != req.tool:
        return None

    val = req.parameters.get(rule.param_name)
    if isinstance(val, (int, float)) and val > rule.max_value:
        is_shadow = rule.shadow_mode or global_shadow
        status = "shadow_blocked" if is_shadow else "blocked"
        return RuleResult(
            status=status,
            outcome=f"Bulk threshold exceeded: Parameter '{rule.param_name}' value ({val}) exceeds maximum allowed ({rule.max_value})",
            matched_rule=f"bulk_thresholds: max {rule.max_value} {rule.param_name}",
        )
    return None


def evaluate_parameter_blocklist(req: ToolCallRequest, rule: ParameterBlocklistRule, global_shadow: bool = False) -> Optional[RuleResult]:
    if rule.tool != req.tool:
        return None

    val = str(req.parameters.get(rule.param_name, "")).lower()
    for pattern in rule.blocklist:
        if pattern.lower() in val:
            is_shadow = rule.shadow_mode or global_shadow
            status = "shadow_blocked" if is_shadow else "blocked"
            return RuleResult(
                status=status,
                outcome=f"Parameter blocklist match: Found forbidden pattern '{pattern}' in parameter '{rule.param_name}'",
                matched_rule=f"parameter_blocklist: '{pattern}'",
            )
    return None
