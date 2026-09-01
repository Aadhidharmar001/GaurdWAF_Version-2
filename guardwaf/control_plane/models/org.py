"""
Multi-Tenant Organization, User, and Membership Models.
"""

from datetime import datetime, timezone
from enum import Enum

from pydantic import BaseModel, Field


class OrgStatus(str, Enum):
    ACTIVE = "ACTIVE"
    SUSPENDED = "SUSPENDED"


class UserStatus(str, Enum):
    ACTIVE = "ACTIVE"
    DISABLED = "DISABLED"


class Role(str, Enum):
    OWNER = "OWNER"
    ADMIN = "ADMIN"
    SECURITY_ADMIN = "SECURITY_ADMIN"
    DEVELOPER = "DEVELOPER"
    AUDITOR = "AUDITOR"


class Organization(BaseModel):
    organization_id: str
    name: str
    slug: str
    status: OrgStatus = OrgStatus.ACTIVE
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class User(BaseModel):
    user_id: str
    email: str
    display_name: str
    status: UserStatus = UserStatus.ACTIVE
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class OrganizationMembership(BaseModel):
    membership_id: str
    organization_id: str
    user_id: str
    role: Role
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
