"""
Durable Resumable HITL State Machine & Workflow Manager.
Handles atomic transitions (PENDING -> APPROVED / DENIED / EXECUTING -> EXECUTED).
"""

import uuid
from datetime import datetime, timezone
from typing import Optional

from guardwaf.core.models import ActionState, PendingAction
from guardwaf.exceptions import (
    GuardWAFActionExpiredError,
    GuardWAFInvalidStateTransitionError,
    GuardWAFSecurityError,
)
from guardwaf.hitl.tokens import HITLTokenManager
from guardwaf.state.base import StateStore
from guardwaf.telemetry.emitter import TelemetryEmitter
from guardwaf.telemetry.events import TelemetryEvent


class HITLWorkflowManager:
    def __init__(
        self,
        state_store: StateStore,
        telemetry: Optional[TelemetryEmitter] = None,
        secret_key: Optional[str] = None,
        token_mgr: Optional[HITLTokenManager] = None,
    ):
        self.state_store = state_store
        self.telemetry = telemetry or TelemetryEmitter()
        self.token_mgr = token_mgr or HITLTokenManager(secret_key=secret_key)

    def approve_action(
        self, pending_action_id: str, approver_id: str = "admin", ttl_seconds: int = 600
    ) -> PendingAction:
        action = self.state_store.get_pending_action(pending_action_id)
        if not action:
            raise GuardWAFSecurityError(
                f"PendingAction '{pending_action_id}' not found.", tool_name="unknown"
            )

        now = datetime.now(timezone.utc)
        if action.status == ActionState.EXPIRED or now > action.expires_at:
            self.state_store.update_pending_action_status(
                pending_action_id, ActionState.EXPIRED, action.status
            )
            raise GuardWAFActionExpiredError(
                f"PendingAction '{pending_action_id}' has expired."
            )

        if action.status != ActionState.PENDING:
            raise GuardWAFInvalidStateTransitionError(
                f"Cannot approve action '{pending_action_id}' with current status '{action.status.value}'."
            )

        # Generate cryptographic approval token
        appr_token = self.token_mgr.generate_approval_token(
            pending_action_id=action.pending_action_id,
            action_intent_digest=action.action_intent_digest,
            parameter_digest=action.parameter_digest,
            session_id=action.session_id,
            agent_id=action.agent_id,
            approver_id=approver_id,
            ttl_seconds=ttl_seconds,
        )

        success = self.state_store.update_pending_action_status(
            pending_action_id=pending_action_id,
            new_status=ActionState.APPROVED,
            expected_old_status=ActionState.PENDING,
            approver_id=approver_id,
            approval_token=appr_token,
        )

        if not success:
            raise GuardWAFInvalidStateTransitionError(
                f"State transition PENDING -> APPROVED failed for '{pending_action_id}'."
            )

        updated_action = self.state_store.get_pending_action(pending_action_id)

        # Emit telemetry
        self.telemetry.emit(
            TelemetryEvent(
                event_type="ACTION_APPROVED",
                event_id=f"evt_{uuid.uuid4().hex[:10]}",
                agent_id=action.agent_id,
                session_id=action.session_id,
                tool_name=action.tool_name,
                parameters=action.parameters,
                parameter_digest=action.parameter_digest,
                status="approved",
                outcome=f"Action approved by {approver_id}",
                pending_action_id=pending_action_id,
            )
        )

        return updated_action

    def deny_action(
        self,
        pending_action_id: str,
        approver_id: str = "admin",
        reason: str = "Denied by human reviewer",
    ) -> PendingAction:
        action = self.state_store.get_pending_action(pending_action_id)
        if not action:
            raise GuardWAFSecurityError(
                f"PendingAction '{pending_action_id}' not found.", tool_name="unknown"
            )

        now = datetime.now(timezone.utc)
        if action.status == ActionState.EXPIRED or now > action.expires_at:
            self.state_store.update_pending_action_status(
                pending_action_id, ActionState.EXPIRED, action.status
            )
            raise GuardWAFActionExpiredError(
                f"PendingAction '{pending_action_id}' has expired."
            )

        if action.status != ActionState.PENDING:
            raise GuardWAFInvalidStateTransitionError(
                f"Cannot deny action '{pending_action_id}' with current status '{action.status.value}'."
            )

        success = self.state_store.update_pending_action_status(
            pending_action_id=pending_action_id,
            new_status=ActionState.DENIED,
            expected_old_status=ActionState.PENDING,
            approver_id=approver_id,
            denied_reason=reason,
        )

        if not success:
            raise GuardWAFInvalidStateTransitionError(
                f"State transition PENDING -> DENIED failed for '{pending_action_id}'."
            )

        updated_action = self.state_store.get_pending_action(pending_action_id)

        self.telemetry.emit(
            TelemetryEvent(
                event_type="ACTION_DENIED",
                event_id=f"evt_{uuid.uuid4().hex[:10]}",
                agent_id=action.agent_id,
                session_id=action.session_id,
                tool_name=action.tool_name,
                parameters=action.parameters,
                parameter_digest=action.parameter_digest,
                status="denied",
                outcome=f"Action denied by {approver_id}: {reason}",
                pending_action_id=pending_action_id,
            )
        )

        return updated_action
