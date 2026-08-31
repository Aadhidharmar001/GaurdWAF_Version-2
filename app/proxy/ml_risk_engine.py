import math
import re
from typing import Dict, Any, List, Tuple
from app.models import ToolCallRequest

# OWASP LLM Top 10 (2025/2026 Guidelines)
OWASP_MAPPING = {
    "prompt_injection": ("LLM01", "Direct/Indirect Prompt Injection"),
    "data_leakage": ("LLM02", "Sensitive Information Disclosure"),
    "excessive_agency": ("LLM06", "Excessive Agency & Unbounded Execution"),
    "unbounded_consumption": ("LLM10", "Unbounded Resource Consumption / Denial of Service"),
    "system_prompt_leak": ("LLM07", "System Prompt Leakage & Governance Bypass"),
    "improper_output": ("LLM05", "Improper Output Handling & Injection Payload")
}

def calculate_shannon_entropy(text: str) -> float:
    """Calculates the Shannon entropy of a string to detect encoded payloads, SQLi, or obfuscated code."""
    if not text:
        return 0.0
    prob = [float(text.count(c)) / len(text) for c in set(text)]
    entropy = -sum([p * math.log2(p) for p in prob])
    return round(entropy, 3)

def scan_payload_for_threat_vectors(parameters: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Inspects tool call parameters for known cyber threat patterns."""
    findings = []
    param_str = str(parameters).lower()

    # 1. SQL Injection / Destructive Query Patterns
    sqli_patterns = [r"drop\s+table", r"truncate\s+table", r"union\s+select", r"exec\s*\(", r"1=1", r"--;"]
    for pat in sqli_patterns:
        if re.search(pat, param_str):
            findings.append({
                "category": "SQL Injection",
                "severity": "CRITICAL",
                "owasp": OWASP_MAPPING["improper_output"],
                "detail": f"Matched malicious SQL execution vector pattern: '{pat}'"
            })
            break

    # 2. Prompt Injection & Jailbreak Markers
    jailbreak_patterns = [r"ignore\s+previous\s+instructions", r"system\s+override", r"jailbreak", r"act\s+as\s+dan", r"bypass\s+guardrails"]
    for pat in jailbreak_patterns:
        if re.search(pat, param_str):
            findings.append({
                "category": "Prompt Injection",
                "severity": "HIGH",
                "owasp": OWASP_MAPPING["prompt_injection"],
                "detail": f"Matched AI Agent override attempt: '{pat}'"
            })
            break

    # 3. Data Exfiltration / PII Exposure Patterns
    pii_patterns = [r"select\s+\*\s+from\s+users", r"credit_card", r"ssn", r"password_hash"]
    for pat in pii_patterns:
        if re.search(pat, param_str):
            findings.append({
                "category": "Data Exfiltration",
                "severity": "HIGH",
                "owasp": OWASP_MAPPING["data_leakage"],
                "detail": f"High risk PII / sensitive table query detected: '{pat}'"
            })
            break

    return findings

def evaluate_ml_risk_score(req: ToolCallRequest, matched_rule: str = None) -> Dict[str, Any]:
    """
    Computes an ML Anomaly & Security Risk Score (0-100%) for an incoming Agent Tool Call.
    Returns composite score, risk level, threat factors, and OWASP categorization.
    """
    base_score = 15.0  # Baseline request score
    risk_factors = []

    # 1. Inspect Payload Entropy
    payload_str = str(req.parameters)
    entropy = calculate_shannon_entropy(payload_str)
    if entropy > 4.5:
        entropy_risk = min((entropy - 4.0) * 15, 30.0)
        base_score += entropy_risk
        risk_factors.append(f"High Payload Entropy ({entropy:.2f}): Obfuscation or complex payload detected.")

    # 2. Threat Vector Deep Scan
    threats = scan_payload_for_threat_vectors(req.parameters)
    for threat in threats:
        if threat["severity"] == "CRITICAL":
            base_score += 45.0
        elif threat["severity"] == "HIGH":
            base_score += 30.0
        risk_factors.append(f"[{threat['owasp'][0]}] {threat['category']}: {threat['detail']}")

    # 3. High-Risk Tool Operations
    destructive_tools = ["delete_records", "execute_query", "drop_table", "execute_command", "send_email"]
    if req.tool in destructive_tools:
        base_score += 15.0
        risk_factors.append(f"High-Impact Action: Tool '{req.tool}' modifies system or external state.")

    # 4. Scope / Context Check
    if req.session_context:
        if not req.session_context.customer_id:
            base_score += 10.0
            risk_factors.append("Unauthenticated / Missing Customer ID in Session Context.")

    # Final Risk Score Clamp
    final_score = min(max(round(base_score, 1), 0.0), 99.9)

    # Determine Risk Level
    if final_score >= 75.0:
        risk_level = "CRITICAL"
    elif final_score >= 50.0:
        risk_level = "HIGH"
    elif final_score >= 25.0:
        risk_level = "MEDIUM"
    else:
        risk_level = "LOW"

    # OWASP Mapping
    primary_owasp = OWASP_MAPPING["excessive_agency"]
    if threats:
        primary_owasp = threats[0]["owasp"]
    elif req.tool == "send_email":
        primary_owasp = OWASP_MAPPING["unbounded_consumption"]

    return {
        "risk_score": final_score,
        "risk_level": risk_level,
        "entropy": entropy,
        "primary_owasp_code": primary_owasp[0],
        "primary_owasp_title": primary_owasp[1],
        "risk_factors": risk_factors,
        "threat_count": len(threats)
    }
