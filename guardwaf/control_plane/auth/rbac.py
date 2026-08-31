"""
Server-Side Role-Based Access Control (RBAC) Permission Enforcement.
"""

from typing import Dict, Set
from guardwaf.control_plane.models.org import Role
from guardwaf.exceptions import GuardWAFSecurityError

# Permission Actions
ACTION_MANAGE_ORG = "manage_org"
ACTION_MANAGE_USERS = "manage_users"
ACTION_REGISTER_AGENT = "register_agent"
ACTION_REVOKE_AGENT = "revoke_agent"
ACTION_CREATE_POLICY = "create_policy"
ACTION_PUBLISH_POLICY = "publish_policy"
ACTION_ROLLBACK_POLICY = "rollback_policy"
ACTION_GENERATE_CREDENTIAL = "generate_credential"
ACTION_APPROVE_HITL = "approve_hitl"
ACTION_TENANT_LOCKDOWN = "tenant_lockdown"
ACTION_VIEW_AUDIT = "view_audit"
ACTION_VIEW_INCIDENTS = "view_incidents"

ROLE_PERMISSIONS: Dict[Role, Set[str]] = {
    Role.OWNER: {
        ACTION_MANAGE_ORG, ACTION_MANAGE_USERS, ACTION_REGISTER_AGENT, ACTION_REVOKE_AGENT,
        ACTION_CREATE_POLICY, ACTION_PUBLISH_POLICY, ACTION_ROLLBACK_POLICY, ACTION_GENERATE_CREDENTIAL,
        ACTION_APPROVE_HITL, ACTION_TENANT_LOCKDOWN, ACTION_VIEW_AUDIT, ACTION_VIEW_INCIDENTS
    },
    Role.ADMIN: {
        ACTION_MANAGE_USERS, ACTION_REGISTER_AGENT, ACTION_REVOKE_AGENT, ACTION_CREATE_POLICY,
        ACTION_PUBLISH_POLICY, ACTION_ROLLBACK_POLICY, ACTION_GENERATE_CREDENTIAL, ACTION_APPROVE_HITL,
        ACTION_VIEW_AUDIT, ACTION_VIEW_INCIDENTS
    },
    Role.SECURITY_ADMIN: {
        ACTION_REVOKE_AGENT, ACTION_CREATE_POLICY, ACTION_PUBLISH_POLICY, ACTION_ROLLBACK_POLICY,
        ACTION_APPROVE_HITL, ACTION_TENANT_LOCKDOWN, ACTION_VIEW_AUDIT, ACTION_VIEW_INCIDENTS
    },
    Role.DEVELOPER: {
        ACTION_REGISTER_AGENT, ACTION_CREATE_POLICY, ACTION_GENERATE_CREDENTIAL, ACTION_VIEW_AUDIT
    },
    Role.AUDITOR: {
        ACTION_VIEW_AUDIT, ACTION_VIEW_INCIDENTS
    }
}

class RBACManager:
    @staticmethod
    def check_permission(role: Role, required_action: str) -> None:
        """
        Enforces server-side permission check. Raises GuardWAFSecurityError if permission is denied.
        """
        allowed_actions = ROLE_PERMISSIONS.get(role, set())
        if required_action not in allowed_actions:
            raise GuardWAFSecurityError(
                f"RBAC DENIED: Role '{role.value}' does not have permission to perform action '{required_action}'.",
                tool_name="rbac"
            )
