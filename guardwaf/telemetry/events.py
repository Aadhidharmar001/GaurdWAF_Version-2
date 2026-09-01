"""
Telemetry Event Schema Definition with Lifecycle Correlation & Identity Attributes.
"""

from datetime import datetime, timezone
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class TelemetryEvent(BaseModel):
    event_type: str = "ACTION_EVALUATED"
    event_id: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    principal_id: Optional[str] = None
    agent_id: str
    tenant_id: Optional[str] = "default"
    authority_id: Optional[str] = None
    authentication_method: Optional[str] = None
    identity_provider: Optional[str] = None
    session_id: str
    tool_name: str
    parameters: Dict[str, Any] = Field(default_factory=dict)
    parameter_digest: Optional[str] = ""
    status: str  # "allowed", "blocked", "pending_hitl", "shadow_blocked", "approved", "denied", "executed"
    outcome: str
    matched_rule: Optional[str] = None
    grant_id: Optional[str] = None
    hitl_id: Optional[str] = None
    pending_action_id: Optional[str] = None
    latency_ms: float = 0.0
    authorization_result: Optional[str] = None
    authorization_failure_reason: Optional[str] = None
