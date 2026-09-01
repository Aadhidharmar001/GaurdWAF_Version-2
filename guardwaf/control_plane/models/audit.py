"""
Immutable Audit Logging Models for Control Plane Operations.
"""

from datetime import datetime, timezone
from typing import Any, Dict

from pydantic import BaseModel, Field


class AuditEvent(BaseModel):
    event_id: str
    event_type: str  # "AGENT_CREATED", "AGENT_REVOKED", "POLICY_PUBLISHED", "POLICY_ROLLED_BACK", "AUTHORITY_REVOKED", "BUNDLE_ISSUED"
    tenant_id: str
    actor_id: str
    resource_type: str  # "agent", "policy", "authority", "bundle"
    resource_id: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = Field(default_factory=dict)
