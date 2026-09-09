"""
Structured Security Events & Parameter Redaction Module.
"""

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field

SENSITIVE_PARAM_NAMES = {
    "password",
    "secret",
    "token",
    "api_key",
    "ssn",
    "credit_card",
    "cvv",
    "auth",
}


def redact_sensitive_parameters(parameters: Dict[str, Any]) -> Dict[str, Any]:
    """
    Recursively redacts sensitive parameter values before emitting telemetry events.
    """
    redacted = {}
    for k, v in parameters.items():
        if k.lower() in SENSITIVE_PARAM_NAMES or any(s in k.lower() for s in ["secret", "password", "token"]):
            redacted[k] = "[REDACTED]"
        elif isinstance(v, dict):
            redacted[k] = redact_sensitive_parameters(v)
        else:
            redacted[k] = v
    return redacted


class StructuredSecurityEvent(BaseModel):
    event_id: str = Field(default_factory=lambda: f"sevt_{uuid.uuid4().hex[:10]}")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    tenant_id: str
    agent_id: str
    principal_id: str = "anonymous"
    session_id: str = "sess_default"
    action_id: str = Field(default_factory=lambda: f"act_{uuid.uuid4().hex[:10]}")
    tool_name: str
    decision: str  # "ALLOW", "BLOCK", "REQUIRE_HITL"
    policy_version: str = "1.0"
    authority_id: Optional[str] = None
    grant_id: Optional[str] = None
    pending_action_id: Optional[str] = None
    parameters_redacted: Dict[str, Any] = Field(default_factory=dict)
    latency_ms: float = 0.0
    correlation_id: Optional[str] = None
