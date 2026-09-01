from typing import Any, Dict, List, Optional, TypedDict


class RiskEvaluationResult(TypedDict):
    fraud_score: float
    confidence_score: float
    risk_level: str
    risk_reasons: List[str]


def evaluate_hitl_risk(
    tool: str, parameters: Dict[str, Any], matched_rule: Optional[str] = None
) -> RiskEvaluationResult:
    """
    Evaluates an HITL-quarantined tool request to determine:
    1. fraud_score: 0.0 - 100.0 (% probability request is fraudulent/unauthorized)
    2. confidence_score: 0.0 - 100.0 (% certainty of detection model)
    3. risk_level: CRITICAL, HIGH, MEDIUM, LOW
    4. risk_reasons: List of explanatory risk drivers
    """
    fraud_score = 45.0  # Base score for any HITL-quarantined action
    confidence_score = 88.0
    risk_reasons: List[str] = []

    params_str = str(parameters).lower()

    # Rule 1: External Email / External Boundary Exfiltration
    recipient = str(parameters.get("recipient", "")).lower()
    if recipient:
        if not recipient.endswith("@aivar.com"):
            fraud_score += 38.0
            confidence_score += 6.0
            risk_reasons.append(f"External recipient exfiltration risk ({recipient})")
        else:
            fraud_score -= 10.0
            confidence_score += 4.0

    # Rule 2: SQL Injection or Destructive Parameters
    sql_keywords = [
        "drop table",
        "truncate",
        "shutdown",
        "delete from",
        "grant all",
        "--",
        "or 1=1",
    ]
    matched_sql = [kw for kw in sql_keywords if kw in params_str]
    if matched_sql:
        fraud_score += 45.0
        confidence_score += 8.0
        risk_reasons.append(f"Destructive SQL pattern detected: '{matched_sql[0]}'")

    # Rule 3: Bulk Record Operations
    record_count = parameters.get("record_count")
    if isinstance(record_count, (int, float)) and record_count > 50:
        fraud_score += 30.0
        confidence_score += 5.0
        risk_reasons.append(f"High-volume bulk operation ({record_count} records)")

    # Rule 4: Data Scope & Cross-Tenant Access
    customer_id = parameters.get("customer_id")
    if customer_id and "cust-999" in str(customer_id).lower():
        fraud_score += 35.0
        confidence_score += 5.0
        risk_reasons.append("Unrestricted customer data scope access")

    # Rule 5: Sensitive Tool Classification
    if tool in ["delete_records", "execute_query"]:
        fraud_score += 15.0
        risk_reasons.append(f"High-privilege tool execution ('{tool}')")

    # Fallback reason if none matched specifically
    if not risk_reasons:
        risk_reasons.append(
            f"Pattern trigger on policy rule: {matched_rule or 'Data Scope Filter'}"
        )

    # Clamp scores
    fraud_score = max(10.0, min(99.0, round(fraud_score, 1)))
    confidence_score = max(75.0, min(98.5, round(confidence_score, 1)))

    # Determine risk level
    if fraud_score >= 85.0:
        risk_level = "CRITICAL"
    elif fraud_score >= 65.0:
        risk_level = "HIGH"
    elif fraud_score >= 40.0:
        risk_level = "MEDIUM"
    else:
        risk_level = "LOW"

    return {
        "fraud_score": fraud_score,
        "confidence_score": confidence_score,
        "risk_level": risk_level,
        "risk_reasons": risk_reasons,
    }
