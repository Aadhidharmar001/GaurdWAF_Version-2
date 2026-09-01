"""
Organization & User Membership Lifecycle Service with Strict Tenant Isolation.
"""

import uuid
from typing import Dict, List, Optional

from guardwaf.control_plane.models.org import (
    Organization,
    OrganizationMembership,
    OrgStatus,
    Role,
    User,
    UserStatus,
)
from guardwaf.exceptions import GuardWAFConfigurationError, GuardWAFSecurityError


class OrgService:
    def __init__(self):
        self._orgs: Dict[str, Organization] = {}
        self._users: Dict[str, User] = {}
        self._memberships: List[OrganizationMembership] = []

    def create_organization(self, name: str, slug: str) -> Organization:
        org_id = f"org_{uuid.uuid4().hex[:10]}"
        org = Organization(
            organization_id=org_id, name=name, slug=slug, status=OrgStatus.ACTIVE
        )
        self._orgs[org_id] = org
        return org

    def create_user(self, email: str, display_name: str) -> User:
        user_id = f"usr_{uuid.uuid4().hex[:10]}"
        user = User(
            user_id=user_id,
            email=email,
            display_name=display_name,
            status=UserStatus.ACTIVE,
        )
        self._users[user_id] = user
        return user

    def add_member(
        self, organization_id: str, user_id: str, role: Role
    ) -> OrganizationMembership:
        if organization_id not in self._orgs:
            raise GuardWAFConfigurationError(
                f"Organization '{organization_id}' not found."
            )
        if user_id not in self._users:
            raise GuardWAFConfigurationError(f"User '{user_id}' not found.")

        mem = OrganizationMembership(
            membership_id=f"mem_{uuid.uuid4().hex[:10]}",
            organization_id=organization_id,
            user_id=user_id,
            role=role,
        )
        self._memberships.append(mem)
        return mem

    def get_membership(
        self, organization_id: str, user_id: str
    ) -> Optional[OrganizationMembership]:
        for m in self._memberships:
            if m.organization_id == organization_id and m.user_id == user_id:
                return m
        return None

    def verify_tenant_isolation(
        self, requesting_org_id: str, target_resource_org_id: str
    ) -> None:
        """
        Server-side tenant isolation check.
        Rejects cross-tenant access attempts.
        """
        if requesting_org_id != target_resource_org_id:
            raise GuardWAFSecurityError(
                f"CROSS-TENANT ACCESS BLOCKED: Tenant '{requesting_org_id}' cannot access resource belonging to tenant '{target_resource_org_id}'.",
                tool_name="tenant_isolation",
            )
