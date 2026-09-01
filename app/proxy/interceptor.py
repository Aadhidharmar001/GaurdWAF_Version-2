from sqlalchemy.orm import Session

from app.models import PolicyConfig, RuleResult, ToolCallRequest
from app.proxy.data_scope import evaluate_data_scope
from app.proxy.ml_risk_engine import evaluate_ml_risk_score
from app.proxy.param_validator import (
    evaluate_bulk_threshold,
    evaluate_parameter_blocklist,
)
from app.proxy.rate_limiter import evaluate_rate_limit
from app.proxy.sequence_guard import evaluate_sequence
from app.proxy.shadow_mode import apply_shadow_mode_transformation


def evaluate_tool_call_request(
    req: ToolCallRequest, policy: PolicyConfig, db: Session
) -> RuleResult:
    global_shadow = policy.shadow_mode
    rules = policy.rules

    final_res = None

    # 1. Rate Limiting Check
    for rule in rules.rate_limits:
        res = evaluate_rate_limit(req, rule, db, global_shadow)
        if res:
            final_res = apply_shadow_mode_transformation(res)
            break

    # 2. Sequence Enforcement Check
    if not final_res:
        for rule in rules.sequences:
            res = evaluate_sequence(req, rule, db, global_shadow)
            if res:
                final_res = apply_shadow_mode_transformation(res)
                break

    # 3. Bulk Operations Threshold Check
    if not final_res:
        for rule in rules.bulk_thresholds:
            res = evaluate_bulk_threshold(req, rule, global_shadow)
            if res:
                final_res = apply_shadow_mode_transformation(res)
                break

    # 4. Data Scope & Session Context Check
    if not final_res:
        for rule in rules.data_scope:
            res = evaluate_data_scope(req, rule, global_shadow)
            if res:
                final_res = apply_shadow_mode_transformation(res)
                break

    # 5. Parameter Blocklist Check
    if not final_res:
        for rule in rules.parameter_blocklist:
            res = evaluate_parameter_blocklist(req, rule, global_shadow)
            if res:
                final_res = apply_shadow_mode_transformation(res)
                break

    if not final_res:
        final_res = RuleResult(status="allowed", outcome="Clear", matched_rule=None)

    # Compute ML Threat & Anomaly Metrics
    ml_eval = evaluate_ml_risk_score(req, final_res.matched_rule)
    final_res.risk_score = ml_eval["risk_score"]
    final_res.risk_level = ml_eval["risk_level"]
    final_res.entropy = ml_eval["entropy"]
    final_res.owasp_code = ml_eval["primary_owasp_code"]
    final_res.risk_factors = ml_eval["risk_factors"]

    return final_res
