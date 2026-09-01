"""
Security Incident Management Data Models.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class IncidentSeverity(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class IncidentStatus(str, Enum):
    OPEN = "OPEN"
    INVESTIGATING = "INVESTIGATING"
    RESOLVED = "RESOLVED"


class Incident(BaseModel):
    incident_id: str
    organization_id: str
    agent_id: str
    title: str
    description: Optional[str] = None
    severity: IncidentSeverity = IncidentSeverity.HIGH
    status: IncidentStatus = IncidentStatus.OPEN
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    resolved_at: Optional[datetime] = None
    resolved_by: Optional[str] = None
    related_event_ids: List[str] = Field(default_factory=list)
    correlation_id: Optional[str] = None
