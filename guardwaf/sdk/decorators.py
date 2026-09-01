"""
Core Python Function Decorator (@protect) for Synchronous and Asynchronous Tools.
Enforces deterministic runtime policy checks, identity authority boundaries, and registers tools for HITL resume execution.
"""

import asyncio
import functools
import inspect
import time
import uuid
from typing import Any, Callable, Optional

from guardwaf.core.canonical import compute_parameter_digest
from guardwaf.core.models import ActionIntent
from guardwaf.exceptions import GuardWAFHITLRequiredError, GuardWAFSecurityError
from guardwaf.sdk.client import GuardWAF
from guardwaf.sdk.context import get_current_execution_context, get_current_session
from guardwaf.telemetry.events import TelemetryEvent


def protect(
    tool_name: Optional[str] = None,
    agent_id: str = "default_agent",
    client: Optional[GuardWAF] = None,
):
    """
    Decorator for wrapping Python tool functions with GuardWAF runtime execution protection.
    Registers tool execution bodies with the GuardWAF client for HITL resume.

    Usage:
        @protect(tool_name="process_refund")
        def process_refund(customer_id: str, amount: float):
            ...
    """

    def decorator(func: Callable) -> Callable:
        target_name = tool_name or func.__name__

        # Auto-register function with default GuardWAF instance
        gw_client = client or GuardWAF.get_default_instance()
        if gw_client:
            gw_client.register_tool(target_name, func)

        if asyncio.iscoroutinefunction(func):

            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs) -> Any:
                active_client = client or GuardWAF.get_default_instance()
                if not active_client:
                    raise RuntimeError(
                        "GuardWAF client is not initialized. Initialize GuardWAF() first."
                    )

                # Ensure tool registration
                active_client.register_tool(target_name, func)

                start_time = time.time()
                # 1. Bind parameters
                sig = inspect.signature(func)
                bound_args = sig.bind(*args, **kwargs)
                bound_args.apply_defaults()
                params = dict(bound_args.arguments)

                # 2. Compute canonical parameter digest
                param_digest = compute_parameter_digest(params)

                # 3. Retrieve context
                exec_ctx = get_current_execution_context()
                session_ctx = get_current_session()
                session_id = (
                    session_ctx.session_id if session_ctx else "untracked_session"
                )
                effective_agent_id = (
                    exec_ctx.agent.agent_id
                    if (exec_ctx and exec_ctx.agent)
                    else agent_id
                )

                # 4. Evaluate Trusted Identity & Delegated Authority Boundary FIRST
                active_client.authority_evaluator.evaluate_authority(
                    exec_ctx, target_name, params
                )

                intent = ActionIntent(
                    intent_id=f"intent_{uuid.uuid4().hex[:10]}",
                    agent_id=effective_agent_id,
                    tool_name=target_name,
                    parameters=params,
                    parameter_digest=param_digest,
                    session_context=session_ctx,
                )

                # 5. Evaluate Declarative Policy Rules
                eval_res = active_client.evaluator.evaluate(intent)
                latency_ms = round((time.time() - start_time) * 1000, 2)

                event = TelemetryEvent(
                    event_type="ACTION_PENDING"
                    if eval_res.status == "pending_hitl"
                    else (
                        "ACTION_BLOCKED"
                        if eval_res.status == "blocked"
                        else "ACTION_ALLOWED"
                    ),
                    event_id=f"evt_{uuid.uuid4().hex[:10]}",
                    principal_id=exec_ctx.principal.principal_id
                    if (exec_ctx and exec_ctx.principal)
                    else None,
                    agent_id=effective_agent_id,
                    tenant_id=exec_ctx.tenant_id if exec_ctx else "default",
                    authority_id=exec_ctx.authority.authority_id
                    if (exec_ctx and exec_ctx.authority)
                    else None,
                    authentication_method=exec_ctx.principal.authentication_method
                    if (exec_ctx and exec_ctx.principal)
                    else "unverified",
                    session_id=session_id,
                    tool_name=target_name,
                    parameters=params,
                    parameter_digest=param_digest,
                    status=eval_res.status,
                    outcome=eval_res.outcome,
                    matched_rule=eval_res.matched_rule,
                    hitl_id=eval_res.hitl_id,
                    pending_action_id=eval_res.pending_action.pending_action_id
                    if eval_res.pending_action
                    else None,
                    latency_ms=latency_ms,
                )

                if eval_res.status == "blocked":
                    active_client.telemetry.emit(event)
                    raise GuardWAFSecurityError(
                        message=f"Action '{target_name}' blocked by GuardWAF policy: {eval_res.outcome}",
                        tool_name=target_name,
                        matched_rule=eval_res.matched_rule,
                        details={
                            "status": eval_res.status,
                            "risk_level": eval_res.risk_level,
                        },
                    )
                elif eval_res.status == "pending_hitl":
                    active_client.telemetry.emit(event)
                    pending_id = (
                        eval_res.pending_action.pending_action_id
                        if eval_res.pending_action
                        else eval_res.hitl_id
                    )
                    raise GuardWAFHITLRequiredError(
                        message=f"Action '{target_name}' requires Human-in-the-Loop approval: {eval_res.outcome}",
                        pending_action_id=pending_id,
                        tool_name=target_name,
                        approval_token=eval_res.hitl_approval_token,
                        hitl_id=pending_id,
                        details={"status": eval_res.status},
                    )

                # 6. Allowed / Shadow Blocked -> Issue Grant & Record State
                del_auth_id = (
                    exec_ctx.authority.authority_id
                    if (exec_ctx and exec_ctx.authority)
                    else None
                )
                grant = active_client.signer.issue_grant(
                    intent, delegated_authority_id=del_auth_id
                )
                event.grant_id = grant.grant_id
                active_client.telemetry.emit(event)

                active_client.state_store.record_tool_call(
                    session_id, target_name, eval_res.status
                )
                active_client.state_store.record_sequence_state(session_id, target_name)

                # Execute wrapped async target function
                return await func(*args, **kwargs)

            return async_wrapper

        else:

            @functools.wraps(func)
            def sync_wrapper(*args, **kwargs) -> Any:
                active_client = client or GuardWAF.get_default_instance()
                if not active_client:
                    raise RuntimeError(
                        "GuardWAF client is not initialized. Initialize GuardWAF() first."
                    )

                # Ensure tool registration
                active_client.register_tool(target_name, func)

                start_time = time.time()
                # 1. Bind parameters
                sig = inspect.signature(func)
                bound_args = sig.bind(*args, **kwargs)
                bound_args.apply_defaults()
                params = dict(bound_args.arguments)

                # 2. Compute canonical parameter digest
                param_digest = compute_parameter_digest(params)

                # 3. Retrieve context
                exec_ctx = get_current_execution_context()
                session_ctx = get_current_session()
                session_id = (
                    session_ctx.session_id if session_ctx else "untracked_session"
                )
                effective_agent_id = (
                    exec_ctx.agent.agent_id
                    if (exec_ctx and exec_ctx.agent)
                    else agent_id
                )
                effective_tenant_id = exec_ctx.tenant_id if exec_ctx else "default"

                # 3b. Local $O(1)$ Revocation Kill Switch Check FIRST
                if (
                    hasattr(active_client, "revocation_client")
                    and active_client.revocation_client
                ):
                    active_client.revocation_client.check_kill_switch_local(
                        effective_tenant_id, effective_agent_id
                    )

                # 4. Evaluate Trusted Identity & Delegated Authority Boundary FIRST
                active_client.authority_evaluator.evaluate_authority(
                    exec_ctx, target_name, params
                )

                intent = ActionIntent(
                    intent_id=f"intent_{uuid.uuid4().hex[:10]}",
                    agent_id=effective_agent_id,
                    tool_name=target_name,
                    parameters=params,
                    parameter_digest=param_digest,
                    session_context=session_ctx,
                )

                # 5. Evaluate Declarative Policy Rules
                eval_res = active_client.evaluator.evaluate(intent)
                latency_ms = round((time.time() - start_time) * 1000, 2)

                event = TelemetryEvent(
                    event_type="ACTION_PENDING"
                    if eval_res.status == "pending_hitl"
                    else (
                        "ACTION_BLOCKED"
                        if eval_res.status == "blocked"
                        else "ACTION_ALLOWED"
                    ),
                    event_id=f"evt_{uuid.uuid4().hex[:10]}",
                    principal_id=exec_ctx.principal.principal_id
                    if (exec_ctx and exec_ctx.principal)
                    else None,
                    agent_id=effective_agent_id,
                    tenant_id=exec_ctx.tenant_id if exec_ctx else "default",
                    authority_id=exec_ctx.authority.authority_id
                    if (exec_ctx and exec_ctx.authority)
                    else None,
                    authentication_method=exec_ctx.principal.authentication_method
                    if (exec_ctx and exec_ctx.principal)
                    else "unverified",
                    session_id=session_id,
                    tool_name=target_name,
                    parameters=params,
                    parameter_digest=param_digest,
                    status=eval_res.status,
                    outcome=eval_res.outcome,
                    matched_rule=eval_res.matched_rule,
                    hitl_id=eval_res.hitl_id,
                    pending_action_id=eval_res.pending_action.pending_action_id
                    if eval_res.pending_action
                    else None,
                    latency_ms=latency_ms,
                )

                if eval_res.status == "blocked":
                    active_client.telemetry.emit(event)
                    raise GuardWAFSecurityError(
                        message=f"Action '{target_name}' blocked by GuardWAF policy: {eval_res.outcome}",
                        tool_name=target_name,
                        matched_rule=eval_res.matched_rule,
                        details={
                            "status": eval_res.status,
                            "risk_level": eval_res.risk_level,
                        },
                    )
                elif eval_res.status == "pending_hitl":
                    active_client.telemetry.emit(event)
                    pending_id = (
                        eval_res.pending_action.pending_action_id
                        if eval_res.pending_action
                        else eval_res.hitl_id
                    )
                    raise GuardWAFHITLRequiredError(
                        message=f"Action '{target_name}' requires Human-in-the-Loop approval: {eval_res.outcome}",
                        pending_action_id=pending_id,
                        tool_name=target_name,
                        approval_token=eval_res.hitl_approval_token,
                        hitl_id=pending_id,
                        details={"status": eval_res.status},
                    )

                # 6. Allowed / Shadow Blocked -> Issue Grant & Record State
                del_auth_id = (
                    exec_ctx.authority.authority_id
                    if (exec_ctx and exec_ctx.authority)
                    else None
                )
                grant = active_client.signer.issue_grant(
                    intent, delegated_authority_id=del_auth_id
                )
                event.grant_id = grant.grant_id
                active_client.telemetry.emit(event)

                active_client.state_store.record_tool_call(
                    session_id, target_name, eval_res.status
                )
                active_client.state_store.record_sequence_state(session_id, target_name)

                # Execute wrapped sync target function
                return func(*args, **kwargs)

            return sync_wrapper

    return decorator
