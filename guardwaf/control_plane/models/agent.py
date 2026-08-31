"""
Control Plane Agent Registration Models & Status Enums.
"""

from enum import Enum
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field

class AgentStatus(str, Enum):
    ACTIVE = "ACTIVE"
    DISABLED = "DISABLED"
    REVOKED = "REVOKED"

class AgentRecord(BaseModel):
    agent_id: str
    tenant_id: str
    name: str
    description: Optional[str] = None
    version: str = "1.0.0"
    environment: str = "production"  # "development", "staging", "production"
    status: AgentStatus = AgentStatus.ACTIVE
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    revoked_at: Optional[datetime] = None
    revoked_by: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
