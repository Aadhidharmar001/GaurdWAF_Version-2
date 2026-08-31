"""
Signed Policy Bundle Model & Digest Cryptographic Schema.
"""

from datetime import datetime, timezone
from typing import Optional, Dict, List, Any
from pydantic import BaseModel, Field

class SignedPolicyBundle(BaseModel):
    """
    Immutable signed policy bundle compiled by the Control Plane for high-speed local SDK enforcement.
    """
    bundle_id: str
    tenant_id: str
    agent_id: str
    environment: str = "production"
    policy_versions: Dict[str, int] = Field(default_factory=dict)
    policy_payload: Dict[str, Any] = Field(default_factory=dict)
    revocation_list: List[str] = Field(default_factory=list)
    issued_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: datetime
    bundle_digest: str
    key_id: str = "k1"
    signature: str

    def is_expired(self) -> bool:
        return datetime.now(timezone.utc) > self.expires_at
