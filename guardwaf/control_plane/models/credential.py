"""
Secure Agent API Credential Schema.
Plaintext API keys are never stored; only SHA-256 hashes are persisted.
"""

from datetime import datetime, timezone
from typing import Optional
from pydantic import BaseModel, Field

class AgentCredential(BaseModel):
    credential_id: str
    organization_id: str
    agent_id: str
    credential_prefix: str  # e.g., "gw_live_abc12"
    credential_hash: str    # SHA-256 hash of full API key
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: Optional[datetime] = None
    revoked_at: Optional[datetime] = None
    last_used_at: Optional[datetime] = None

class IssuedCredentialResponse(BaseModel):
    credential_id: str
    organization_id: str
    agent_id: str
    plaintext_api_key: str  # Displayed ONLY ONCE to developer
    created_at: datetime
