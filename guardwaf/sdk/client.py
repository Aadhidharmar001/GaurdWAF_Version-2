"""
GuardWAF Primary Client Class.
Holds policy configuration, state store, signer, hitl_workflow manager, tool registry, and telemetry emitter.
Provides the safe, atomic resume() API for resuming HITL-approved actions.
"""

import asyncio
import inspect
import os
import time
import uuid
from typing import Any, Callable, Dict, List, Optional

from guardwaf.core.authority import DelegatedAuthority
from guardwaf.core.canonical import compute_parameter_digest
from guardwaf.core.grants import GrantSigner
from guardwaf.core.keys import KeyManager
from guardwaf.core.models import (
    ActionState,
    PendingAction,
    PolicyConfig,
    SessionContext,
)
from guardwaf.core.policy import load_policy_from_yaml
from guardwaf.engine.authority_evaluator import AuthorityEvaluator
from guardwaf.engine.evaluator import ActionEvaluator
from guardwaf.exceptions import (
    GuardWAFActionExpiredError,
    GuardWAFAlreadyExecutedError,
    GuardWAFConfigurationError,
    GuardWAFInvalidStateTransitionError,
    GuardWAFSecurityError,
)
from guardwaf.hitl.manager import HITLWorkflowManager
from guardwaf.hitl.tokens import HITLTokenManager
from guardwaf.identity.models import AgentIdentity, VerifiedPrincipal
from guardwaf.sdk.context import (
    get_current_session,
    session,
    verified_session,
)
from guardwaf.sdk.policy_client import PolicyClient
from guardwaf.state.base import StateStore
from guardwaf.state.memory import MemoryStateStore
from guardwaf.telemetry.emitter import TelemetryEmitter
from guardwaf.telemetry.events import TelemetryEvent

_DEFAULT_INSTANCE: Optional["GuardWAF"] = None


class GuardWAF:
    def __init__(
        self,
        config_path: Optional[str] = None,
        policy_path: Optional[str] = None,
        policy: Optional[PolicyConfig] = None,
        policy_client: Optional[PolicyClient] = None,
        state_store: Optional[StateStore] = None,
        secret_key: Optional[str] = None,
        key_id: str = "k1",
        keyring: Optional[Dict[str, str]] = None,
        environment: Optional[str] = None,
        strict_identity: bool = False,
    ):
        self.strict_identity = strict_identity
        self.policy_client = policy_client
        config_path = config_path or policy_path

        if policy:
            self._static_policy = policy
        elif policy_client and policy_client.get_active_policy():
            self._static_policy = policy_client.get_active_policy()
        elif config_path:
            self._static_policy = load_policy_from_yaml(config_path)
        else:
            default_yaml = "rules.yaml"
            if os.path.exists(default_yaml):
                self._static_policy = load_policy_from_yaml(default_yaml)
            elif policy_client:
                self._static_policy = PolicyConfig(metadata={"policy_name": "empty"}, rules={})
            else:
                raise GuardWAFConfigurationError("GuardWAF requires a valid config_path, policy instance, or policy_client.")

        self.key_manager = KeyManager(
            secret_key=secret_key,
            key_id=key_id,
            keyring=keyring,
            environment=environment,
        )
        self.state_store = state_store or MemoryStateStore()
        self.signer = GrantSigner(key_manager=self.key_manager)
        self.token_mgr = HITLTokenManager(key_manager=self.key_manager)
        self._evaluator = ActionEvaluator(policy=self._static_policy, state_store=self.state_store)
        self.authority_evaluator = AuthorityEvaluator(strict_mode=self.strict_identity)
        self.telemetry = TelemetryEmitter()
        self.hitl_workflow = HITLWorkflowManager(
            state_store=self.state_store,
            telemetry=self.telemetry,
            token_mgr=self.token_mgr,
        )
        from guardwaf.sdk.revocation_client import RevocationClient
        from guardwaf.sdk.runtime_adapter import AgentRuntimeAdapter

        self.revocation_client = RevocationClient(key_manager=self.key_manager)
        self.runtime_adapter = AgentRuntimeAdapter(waf=self)
        self._tool_registry: Dict[str, Callable] = {}

        global _DEFAULT_INSTANCE
        _DEFAULT_INSTANCE = self

    @property
    def policy(self) -> PolicyConfig:

        if self.policy_client:
            active = self.policy_client.get_active_policy()
            if active:
                return active
        return self._static_policy

    @property
    def evaluator(self) -> ActionEvaluator:
        self._evaluator.policy = self.policy
        return self._evaluator

    @classmethod
    def get_default_instance(cls) -> Optional["GuardWAF"]:
        return _DEFAULT_INSTANCE

    def register_tool(self, tool_name: str, func: Callable) -> None:
        """Registers a tool function implementation for HITL resume execution."""
        self._tool_registry[tool_name] = func

    def session(
        self,
        session_id: str,
        principal_id: Optional[str] = None,
        customer_id: Optional[str] = None,
        tenant_id: Optional[str] = "default",
        user_role: Optional[str] = "user",
        allowed_scope_ids: Optional[list] = None,
    ):
        return session(
            session_id=session_id,
            principal_id=principal_id,
            customer_id=customer_id,
            tenant_id=tenant_id,
            user_role=user_role,
            allowed_scope_ids=allowed_scope_ids,
        )

    def verified_session(
        self,
        principal: VerifiedPrincipal,
        agent: Optional[AgentIdentity] = None,
        authority: Optional[DelegatedAuthority] = None,
        session_id: Optional[str] = None,
        tenant_id: Optional[str] = None,
        customer_id: Optional[str] = None,
    ):
        return verified_session(
            principal=principal,
            agent=agent,
            authority=authority,
            session_id=session_id,
            tenant_id=tenant_id,
            customer_id=customer_id,
        )

    def approve_pending_action(self, pending_action_id: str, approver_id: str = "admin") -> PendingAction:
        """Approve a pending action, producing a cryptographically signed approval token."""
        return self.hitl_workflow.approve_action(pending_action_id, approver_id=approver_id)

    def deny_pending_action(
        self,
        pending_action_id: str,
        approver_id: str = "admin",
        reason: str = "Denied by human reviewer",
    ) -> PendingAction:
        """Deny a pending action."""
        return self.hitl_workflow.deny_action(pending_action_id, approver_id=approver_id, reason=reason)

    def list_pending_actions(self, status: Optional[ActionState] = None) -> List[PendingAction]:
        """Lists pending actions."""
        return self.state_store.list_pending_actions(status=status)

    async def resume(
        self,
        pending_action_id: str,
        approval_token: str,
        session_context: Optional[SessionContext] = None,
    ) -> Any:
        """
        Safely and atomically resumes execution of an approved PendingAction.
        Guarantees EXACTLY-ONCE execution. Replays, parameter changes, wrong sessions, or expired actions will be rejected.
        """
        start_time = time.time()

        # 1. Telemetry
        self.telemetry.emit(
            TelemetryEvent(
                event_type="ACTION_RESUME_REQUESTED",
                event_id=f"evt_{uuid.uuid4().hex[:10]}",
                agent_id="unknown",
                session_id="unknown",
                tool_name="unknown",
                status="resuming",
                outcome=f"Resume requested for '{pending_action_id}'",
                pending_action_id=pending_action_id,
            )
        )

        # 2. Retrieve PendingAction
        action = self.state_store.get_pending_action(pending_action_id)
        if not action:
            raise GuardWAFSecurityError(f"PendingAction '{pending_action_id}' not found.", tool_name="unknown")

        # 3. Check State
        if action.status == ActionState.DENIED:
            raise GuardWAFSecurityError(
                f"Action '{pending_action_id}' was DENIED and cannot be resumed.",
                tool_name=action.tool_name,
            )
        if action.status == ActionState.EXPIRED:
            raise GuardWAFActionExpiredError(f"Action '{pending_action_id}' has EXPIRED and cannot be resumed.")
        if action.status in [ActionState.EXECUTED, ActionState.EXECUTING]:
            raise GuardWAFAlreadyExecutedError(
                f"Action '{pending_action_id}' has already been executed.",
                tool_name=action.tool_name,
                pending_action_id=pending_action_id,
            )
        if action.status != ActionState.APPROVED:
            raise GuardWAFInvalidStateTransitionError(
                f"Action '{pending_action_id}' is not in APPROVED state (current: {action.status.value})."
            )

        # 4. Context Verification (Session & Agent identity)
        ctx = session_context or get_current_session()
        if ctx:
            if ctx.session_id != action.session_id:
                raise GuardWAFSecurityError(
                    f"Resume session mismatch: Action belongs to session '{action.session_id}', but caller is in session '{ctx.session_id}'.",
                    tool_name=action.tool_name,
                )

        # 5. Verify Cryptographic Approval Token
        token_valid = self.hitl_workflow.token_mgr.verify_approval_token(
            token=approval_token,
            pending_action_id=action.pending_action_id,
            action_intent_digest=action.action_intent_digest,
            parameter_digest=action.parameter_digest,
            session_id=action.session_id,
            agent_id=action.agent_id,
        )
        if not token_valid:
            raise GuardWAFSecurityError(
                f"Invalid, expired, or forged approval token for action '{pending_action_id}'.",
                tool_name=action.tool_name,
            )

        # 6. Verify Parameter Digest Integrity
        current_param_digest = compute_parameter_digest(action.parameters)
        if current_param_digest != action.parameter_digest:
            raise GuardWAFSecurityError(
                f"Parameter digest mismatch for action '{pending_action_id}'. Parameters were tampered with.",
                tool_name=action.tool_name,
            )

        # 7. Atomic Claim Execution (APPROVED -> EXECUTING)
        claimed = self.state_store.update_pending_action_status(
            pending_action_id=pending_action_id,
            new_status=ActionState.EXECUTING,
            expected_old_status=ActionState.APPROVED,
        )
        if not claimed:
            raise GuardWAFAlreadyExecutedError(
                f"Action '{pending_action_id}' was claimed by another thread/worker.",
                tool_name=action.tool_name,
                pending_action_id=pending_action_id,
            )

        self.telemetry.emit(
            TelemetryEvent(
                event_type="ACTION_EXECUTION_STARTED",
                event_id=f"evt_{uuid.uuid4().hex[:10]}",
                agent_id=action.agent_id,
                session_id=action.session_id,
                tool_name=action.tool_name,
                parameters=action.parameters,
                parameter_digest=action.parameter_digest,
                status="executing",
                outcome="Atomic execution claimed",
                pending_action_id=pending_action_id,
            )
        )

        # 8. Retrieve registered tool implementation
        func = self._tool_registry.get(action.tool_name)
        if not func:
            # Rollback state if tool implementation is missing
            self.state_store.update_pending_action_status(pending_action_id, ActionState.APPROVED, ActionState.EXECUTING)
            raise GuardWAFConfigurationError(
                f"No execution body registered for tool '{action.tool_name}'. Decorate the function with @protect()."
            )

        # Extract unwrapped original function body if decorated
        target_func = getattr(func, "__wrapped__", func)

        # 9. Execute original tool function
        try:
            if inspect.iscoroutinefunction(target_func):
                result = await target_func(**action.parameters)
            else:
                result = target_func(**action.parameters)

            latency_ms = round((time.time() - start_time) * 1000, 2)

            # 10. Mark State EXECUTING -> EXECUTED
            self.state_store.update_pending_action_status(
                pending_action_id=pending_action_id,
                new_status=ActionState.EXECUTED,
                expected_old_status=ActionState.EXECUTING,
            )
            self.state_store.record_tool_call(action.session_id, action.tool_name, "allowed")
            self.state_store.record_sequence_state(action.session_id, action.tool_name)

            self.telemetry.emit(
                TelemetryEvent(
                    event_type="ACTION_EXECUTED",
                    event_id=f"evt_{uuid.uuid4().hex[:10]}",
                    agent_id=action.agent_id,
                    session_id=action.session_id,
                    tool_name=action.tool_name,
                    parameters=action.parameters,
                    parameter_digest=action.parameter_digest,
                    status="executed",
                    outcome="Action executed successfully upon HITL resume",
                    pending_action_id=pending_action_id,
                    latency_ms=latency_ms,
                )
            )

            return result

        except Exception as e:
            self.telemetry.emit(
                TelemetryEvent(
                    event_type="ACTION_EXECUTION_FAILED",
                    event_id=f"evt_{uuid.uuid4().hex[:10]}",
                    agent_id=action.agent_id,
                    session_id=action.session_id,
                    tool_name=action.tool_name,
                    parameters=action.parameters,
                    parameter_digest=action.parameter_digest,
                    status="failed",
                    outcome=f"Tool execution failed during resume: {e!s}",
                    pending_action_id=pending_action_id,
                )
            )
            raise e

    def resume_sync(
        self,
        pending_action_id: str,
        approval_token: str,
        session_context: Optional[SessionContext] = None,
    ) -> Any:
        """Synchronous wrapper for resume()."""
        return asyncio.run(self.resume(pending_action_id, approval_token, session_context))


def set_default_instance(instance: GuardWAF) -> None:
    global _DEFAULT_INSTANCE
    _DEFAULT_INSTANCE = instance


def get_default_instance() -> Optional[GuardWAF]:
    return _DEFAULT_INSTANCE
