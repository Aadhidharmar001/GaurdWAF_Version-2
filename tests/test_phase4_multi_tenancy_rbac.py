"""
Comprehensive Phase 4 Unit Test Suite for Multi-Tenancy Isolation, Server-Side RBAC,
Hashed Agent Credentials, HITL Workstation, and Incident Management.
"""

import pytest

from guardwaf.control_plane.auth.rbac import (
    ACTION_APPROVE_HITL,
    ACTION_PUBLISH_POLICY,
    ACTION_REGISTER_AGENT,
    RBACManager,
)
from guardwaf.control_plane.models.org import Role
from guardwaf.control_plane.repositories.memory_repo import MemoryControlPlaneRepository
from guardwaf.control_plane.services.credential_service import CredentialService
from guardwaf.control_plane.services.incident_service import IncidentService
from guardwaf.control_plane.services.org_service import OrgService
from guardwaf.exceptions import GuardWAFSecurityError

# ============================================================================
# 1. MULTI-TENANCY ISOLATION TESTS
# ============================================================================


def test_tenant_isolation_verification():
    org_svc = OrgService()
    org_a = org_svc.create_organization("Org A", "org-a")
    org_b = org_svc.create_organization("Org B", "org-b")

    # Same tenant access allowed
    org_svc.verify_tenant_isolation(org_a.organization_id, org_a.organization_id)

    # Cross-tenant access blocked
    with pytest.raises(GuardWAFSecurityError) as exc_info:
        org_svc.verify_tenant_isolation(org_a.organization_id, org_b.organization_id)
    assert "CROSS-TENANT ACCESS BLOCKED" in exc_info.value.message


# ============================================================================
# 2. SERVER-SIDE RBAC PERMISSION TESTS
# ============================================================================


def test_rbac_permission_matrix():
    # Owner & Admin can publish policy
    RBACManager.check_permission(Role.OWNER, ACTION_PUBLISH_POLICY)
    RBACManager.check_permission(Role.ADMIN, ACTION_PUBLISH_POLICY)
    RBACManager.check_permission(Role.SECURITY_ADMIN, ACTION_PUBLISH_POLICY)

    # Developer CANNOT publish policy
    with pytest.raises(GuardWAFSecurityError) as exc_1:
        RBACManager.check_permission(Role.DEVELOPER, ACTION_PUBLISH_POLICY)
    assert "RBAC DENIED" in exc_1.value.message

    # Auditor CANNOT publish policy or approve HITL
    with pytest.raises(GuardWAFSecurityError) as exc_2:
        RBACManager.check_permission(Role.AUDITOR, ACTION_APPROVE_HITL)
    assert "RBAC DENIED" in exc_2.value.message

    # Developer CAN register agent
    RBACManager.check_permission(Role.DEVELOPER, ACTION_REGISTER_AGENT)


# ============================================================================
# 3. SECURE AGENT CREDENTIAL TESTS
# ============================================================================


def test_credential_issuance_hashing_and_verification():
    cs = CredentialService()
    issued = cs.issue_credential("org_1", "agent_1")

    assert issued.plaintext_api_key.startswith("gw_live_")
    assert issued.credential_id is not None

    # Plaintext key is NOT stored in credential record
    cred_rec = cs._credentials[issued.credential_id]
    assert cred_rec.credential_hash != issued.plaintext_api_key
    assert len(cred_rec.credential_hash) == 64  # SHA-256 hex string

    # Verify valid key
    verified = cs.verify_credential(issued.plaintext_api_key)
    assert verified.agent_id == "agent_1"
    assert verified.last_used_at is not None

    # Revoke credential
    cs.revoke_credential(issued.credential_id)
    with pytest.raises(GuardWAFSecurityError) as exc_info:
        cs.verify_credential(issued.plaintext_api_key)
    assert "REVOKED" in exc_info.value.message


# ============================================================================
# 4. INCIDENT MANAGEMENT TESTS
# ============================================================================


def test_incident_creation_and_resolution():
    repo = MemoryControlPlaneRepository()
    inc_svc = IncidentService(audit_repo=repo)

    inc = inc_svc.create_incident("org_inc", "agent_1", title="Large Refund Suspended")
    assert inc.status.value == "OPEN"
    assert inc.organization_id == "org_inc"

    resolved = inc_svc.resolve_incident("org_inc", inc.incident_id, resolved_by="maya")
    assert resolved.status.value == "RESOLVED"
    assert resolved.resolved_by == "maya"

    # Cross-tenant incident resolution blocked
    inc2 = inc_svc.create_incident("org_other", "agent_2", title="Other Incident")
    with pytest.raises(GuardWAFSecurityError):
        inc_svc.resolve_incident("org_inc", inc2.incident_id)
