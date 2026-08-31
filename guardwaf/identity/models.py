"""
Immutable VerifiedPrincipal and AgentIdentity Data Models.
"""

from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict

class VerifiedPrincipal(BaseModel):
    """
    Immutable representation of a cryptographically verified human or system principal.
    Must NEVER be constructed directly from untrusted LLM tool parameters.
    """
    model_config = ConfigDict(frozen=True)

    principal_id: str
    tenant_id: str = "default"
    subject: str
    issuer: str = "guardwaf"
    audience: str = "guardwaf-api"
    authentication_method: str = "jwt"  # "jwt", "oidc", "static", "mtls"
    roles: List[str] = Field(default_factory=list)
    permissions: List[str] = Field(default_factory=list)
    issued_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: Optional[datetime] = None
    claims: Dict[str, Any] = Field(default_factory=dict)

    def is_expired(self) -> bool:
        if self.expires_at is None:
            return False
        return datetime.now(timezone.utc) > self.expires_at

    def has_permission(self, perm: str) -> bool:
        return perm in self.permissions

    def has_role(self, role: str) -> bool:
        return role in self.roles

class AgentIdentity(BaseModel):
    """
    Immutable identity of the autonomous agent executing the action.
    Distinguishes WHO the human principal is from WHICH agent is running.
    """
    model_config = ConfigDict(frozen=True)

    agent_id: str
    agent_type: str = "autonomous_agent"
    tenant_id: str = "default"
    version: str = "1.0.0"
    metadata: Dict[str, Any] = Field(default_factory=dict)

class IdentityCredentials(BaseModel):
    """
    Container for identity credentials presented to an IdentityProvider.
    """
    token_type: str = "bearer"  # "bearer", "jwt", "static"
    raw_token: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
