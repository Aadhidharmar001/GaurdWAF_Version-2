"""
Control Plane Authority Lifecycle Management Models.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class AuthorityStatus(str, Enum):
    ISSUED = "ISSUED"
    ACTIVE = "ACTIVE"
    REVOKED = "REVOKED"
    EXPIRED = "EXPIRED"


class CentralAuthorityRecord(BaseModel):
    authority_id: str
    tenant_id: str
    principal_id: str
    agent_id: str
    allowed_actions: List[str] = Field(default_factory=list)
    constraints: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    status: AuthorityStatus = AuthorityStatus.ACTIVE
    issued_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: datetime
    revoked_at: Optional[datetime] = None
    revoked_by: Optional[str] = None
    revocation_reason: Optional[str] = None
