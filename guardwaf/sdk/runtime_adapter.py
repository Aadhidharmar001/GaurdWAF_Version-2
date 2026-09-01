"""
Framework-Independent Agent Runtime Adapter.
Provides a unified authorization interface for all agent frameworks (LangChain, CrewAI, MCP, Custom).
Routes 100% of security evaluations through the single GuardWAF core engine.
"""

import uuid
from typing import Optional, Tuple

from guardwaf.core.action_envelope import ActionEnvelope
from guardwaf.core.grants import ActionGrant
from guardwaf.core.models import ActionIntent, PendingAction, SessionContext
from guardwaf.sdk.client import GuardWAF
from guardwaf.sdk.context import get_current_execution_context
from guardwaf.sdk.revocation_client import RevocationClient


class AgentRuntimeAdapter:
    """
    Universal agent runtime adapter for GuardWAF authorization.
    All framework wrappers translate tool calls into an ActionEnvelope and call authorize_action().
    """

    def __init__(
        self, waf: GuardWAF, revocation_client: Optional[RevocationClient] = None
    ):
        self.waf = waf
        self.revocation_client = revocation_client or RevocationClient(
            key_manager=waf.key_manager
        )

    def authorize_action(
        self, envelope: ActionEnvelope
    ) -> Tuple[bool, Optional[str], Optional[ActionGrant], Optional[PendingAction]]:
        """
        Single Core Authorization Entry Point.
        1. Check Local O(1) Kill Switches (Agent Revocation & Tenant Lockdown).
        2. Check Verified Execution Context & Authority.
        3. Evaluate GuardWAF Policy Rules.
        4. Produce ALLOW (ActionGrant), BLOCK (raise/return false), or HITL (PendingAction).
        """
        # 1. Local O(1) Hot-Path Kill Switch Check
        self.revocation_client.check_kill_switch_local(
            envelope.tenant_id, envelope.agent_id
        )

        # 2. Check Execution Context Authority
        exec_ctx = get_current_execution_context()
        if exec_ctx and exec_ctx.principal:
            self.waf.authority_evaluator.evaluate(
                principal=exec_ctx.principal,
                agent=exec_ctx.agent,
                authority=exec_ctx.authority,
                tool_name=envelope.tool_name,
                parameters=envelope.parameters,
            )

        # 3. Construct ActionIntent for Policy Evaluation
        s_ctx = SessionContext(
            session_id=envelope.session_id,
            principal_id=envelope.principal_id,
            tenant_id=envelope.tenant_id,
        )

        intent = ActionIntent(
            intent_id=f"intent_{uuid.uuid4().hex[:10]}",
            agent_id=envelope.agent_id,
            tool_name=envelope.tool_name,
            parameters=envelope.parameters,
            parameter_digest=envelope.parameter_digest,
            session_context=s_ctx,
        )

        # 4. Evaluate Policy Rules
        rule_res = self.waf.evaluator.evaluate(intent)
        status = rule_res.status.lower()

        if status == "allowed":
            grant = self.waf.signer.issue_grant(intent)
            return True, None, grant, None

        elif "hitl" in status:
            pending_action = rule_res.pending_action
            return False, f"HITL Required: {rule_res.outcome}", None, pending_action

        else:  # "blocked", "shadow_blocked"
            return (
                False,
                f"Action '{envelope.tool_name}' blocked by GuardWAF policy: {rule_res.outcome}",
                None,
                None,
            )

    def evaluate(self, envelope: ActionEnvelope):
        """Convenience method returning a decision tuple with .allowed and .reason properties."""
        from collections import namedtuple

        RuntimeDecision = namedtuple(
            "RuntimeDecision", ["allowed", "reason", "grant", "pending"]
        )
        allowed, reason, grant, pending = self.authorize_action(envelope)
        return RuntimeDecision(
            allowed=allowed, reason=reason, grant=grant, pending=pending
        )
