import re
from typing import Optional

from app.models import DataScopeRule, RuleResult, ToolCallRequest


def evaluate_data_scope(
    req: ToolCallRequest, rule: DataScopeRule, global_shadow: bool = False
) -> Optional[RuleResult]:
    if rule.tool != req.tool:
        return None

    is_shadow = rule.shadow_mode or global_shadow
    param_val = req.parameters.get(rule.param_name)

    if rule.check_session_customer_id or rule.param_name == "customer_id":
        if req.session_context and req.session_context.customer_id:
            session_cust_id = str(req.session_context.customer_id)
            target_cust_id = str(param_val) if param_val is not None else None

            if target_cust_id != session_cust_id:
                status = "shadow_blocked" if is_shadow else "blocked"
                return RuleResult(
                    status=status,
                    outcome=f"Data Scope Mismatch: Session customer_id '{session_cust_id}' does not match requested data customer_id '{target_cust_id}'",
                    matched_rule=f"data_scope: session_customer_id match required ({rule.param_name})",
                )

    if (
        req.session_context
        and req.session_context.allowed_scope_ids
        and param_val is not None
    ):
        allowed_scope_ids = {
            str(scope_id) for scope_id in req.session_context.allowed_scope_ids
        }
        if str(param_val) not in allowed_scope_ids:
            status = "shadow_blocked" if is_shadow else "blocked"
            return RuleResult(
                status=status,
                outcome=f"Declared Scope Violation: Parameter '{rule.param_name}' references '{param_val}' outside allowed scope {sorted(allowed_scope_ids)}",
                matched_rule=f"data_scope: declared_scope allow-list ({rule.param_name})",
            )

    if rule.pattern and param_val is not None:
        if re.match(rule.pattern, str(param_val)):
            if rule.action == "require_hitl":
                status = "shadow_blocked" if is_shadow else "pending_hitl"
                return RuleResult(
                    status=status,
                    outcome=f"Data Scope Pattern Trigger: Parameter '{rule.param_name}' matched pattern '{rule.pattern}'",
                    matched_rule=f"data_scope: pattern trigger ({rule.param_name})",
                )
            else:
                status = "shadow_blocked" if is_shadow else "blocked"
                return RuleResult(
                    status=status,
                    outcome=f"Data Scope Violation: Parameter '{rule.param_name}' matched restricted pattern '{rule.pattern}'",
                    matched_rule=f"data_scope: pattern block ({rule.param_name})",
                )

    return None
