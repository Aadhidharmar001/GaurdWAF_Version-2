"""
Control Plane Enterprise Policy Management Models, Versioning, and Assignments.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class PolicyStatus(str, Enum):
    DRAFT = "DRAFT"
    VALIDATED = "VALIDATED"
    PUBLISHED = "PUBLISHED"
    ACTIVE = "ACTIVE"


class PolicyVersion(BaseModel):
    version_id: str
    policy_id: str
    version_number: int
    rules: Dict[str, Any]  # Serializable policy rules payload
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    created_by: str = "admin"
    content_digest: str  # SHA-256 hash of rules content


class PolicyRecord(BaseModel):
    policy_id: str
    tenant_id: str
    name: str
    description: Optional[str] = None
    status: PolicyStatus = PolicyStatus.DRAFT
    active_version: Optional[int] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    created_by: str = "admin"


class PolicyAssignment(BaseModel):
    assignment_id: str
    tenant_id: str
    agent_id: Optional[str] = None  # None indicates Tenant-wide policy
    environment: str = "production"
    policy_id: str
    version_number: Optional[int] = None  # None indicates active version
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
