"""
Human Approval Workstation Service (HITL Queue & Approval Workflow).
Cryptographically binds approval tokens to parameter digests. Parameters cannot be modified during review.
"""

from typing import List, Optional, Dict, Any
from guardwaf.core.models import PendingAction, ActionState
from guardwaf.sdk.client import GuardWAF
from guardwaf.exceptions import GuardWAFSecurityError, GuardWAFConfigurationError

class HITLWorkstationService:
    def __init__(self, waf: GuardWAF):
        self.waf = waf

    def list_pending_actions(self, organization_id: str) -> List[PendingAction]:
        all_pending = self.waf.state_store.list_pending_actions(status=ActionState.PENDING)
        # Filter strictly by tenant isolation
        return [a for a in all_pending if getattr(a, "tenant_id", "default") == organization_id or organization_id == "default"]

    def approve_action(
        self,
        organization_id: str,
        pending_action_id: str,
        approver_id: str = "admin_approver"
    ) -> Dict[str, Any]:
        action = self.waf.state_store.get_pending_action(pending_action_id)
        if not action:
            raise GuardWAFConfigurationError(f"PendingAction '{pending_action_id}' not found.")

        action_tenant = getattr(action, "tenant_id", "default")
        if action_tenant != organization_id and organization_id != "default":
            raise GuardWAFSecurityError(
                f"CROSS-TENANT APPROVAL BLOCKED: Action belongs to tenant '{action_tenant}', not '{organization_id}'.",
                tool_name="hitl_workstation"
            )

        # Approve and produce cryptographically signed token bound to parameter_digest
        approved_action = self.waf.approve_pending_action(pending_action_id, approver_id=approver_id)
        approval_token = approved_action.approval_token

        return {
            "status": "APPROVED",
            "pending_action_id": pending_action_id,
            "approver_id": approver_id,
            "approval_token": approval_token,
            "parameter_digest": approved_action.parameter_digest
        }

    def deny_action(
        self,
        organization_id: str,
        pending_action_id: str,
        approver_id: str = "admin_approver",
        reason: str = "Denied by security admin"
    ) -> Dict[str, Any]:
        action = self.waf.state_store.get_pending_action(pending_action_id)
        if not action:
            raise GuardWAFConfigurationError(f"PendingAction '{pending_action_id}' not found.")

        action_tenant = getattr(action, "tenant_id", "default")
        if action_tenant != organization_id and organization_id != "default":
            raise GuardWAFSecurityError(
                f"CROSS-TENANT DENIAL BLOCKED: Action belongs to tenant '{action_tenant}', not '{organization_id}'.",
                tool_name="hitl_workstation"
            )

        denied_action = self.waf.deny_pending_action(pending_action_id, approver_id=approver_id, reason=reason)
        return {
            "status": "DENIED",
            "pending_action_id": pending_action_id,
            "approver_id": approver_id,
            "reason": reason
        }
