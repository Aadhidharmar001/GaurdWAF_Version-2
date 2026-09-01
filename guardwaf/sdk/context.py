"""
Thread-safe and Async-safe Execution Context Manager using Python contextvars.
Manages VerifiedPrincipal, AgentIdentity, DelegatedAuthority, and Session Isolation.
"""

import uuid
from collections.abc import Generator
from contextlib import contextmanager
from contextvars import ContextVar
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field

from guardwaf.core.authority import DelegatedAuthority
from guardwaf.core.models import SessionContext
from guardwaf.identity.models import AgentIdentity, VerifiedPrincipal


class ExecutionContext(BaseModel):
    """
    Immutable trust-aware ExecutionContext binding VerifiedPrincipal, AgentIdentity, DelegatedAuthority, and SessionID.
    """

    model_config = ConfigDict(frozen=True)

    principal: Optional[VerifiedPrincipal] = None
    agent: Optional[AgentIdentity] = None
    authority: Optional[DelegatedAuthority] = None
    session_id: str
    tenant_id: str = "default"
    metadata: Dict[str, Any] = Field(default_factory=dict)

    def to_legacy_session_context(self) -> SessionContext:

        p_id = self.principal.principal_id if self.principal else None
        role = (
            self.principal.roles[0]
            if (self.principal and self.principal.roles)
            else "user"
        )
        return SessionContext(
            session_id=self.session_id,
            principal_id=p_id,
            tenant_id=self.tenant_id,
            user_role=role,
            customer_id=self.metadata.get("customer_id"),
        )


_CURRENT_EXECUTION_CONTEXT: ContextVar[Optional[ExecutionContext]] = ContextVar(
    "_CURRENT_EXECUTION_CONTEXT", default=None
)
_CURRENT_SESSION: ContextVar[Optional[SessionContext]] = ContextVar(
    "_CURRENT_SESSION", default=None
)


def get_current_execution_context() -> Optional[ExecutionContext]:
    """Retrieves the active ExecutionContext for the current thread/async task."""
    return _CURRENT_EXECUTION_CONTEXT.get()


def get_current_session() -> Optional[SessionContext]:
    """Retrieves the active SessionContext for the current thread/async task (backward compatibility)."""
    exec_ctx = _CURRENT_EXECUTION_CONTEXT.get()
    if exec_ctx:
        return exec_ctx.to_legacy_session_context()
    return _CURRENT_SESSION.get()


@contextmanager
def verified_session(
    principal: VerifiedPrincipal,
    agent: Optional[AgentIdentity] = None,
    authority: Optional[DelegatedAuthority] = None,
    session_id: Optional[str] = None,
    tenant_id: Optional[str] = None,
    customer_id: Optional[str] = None,
) -> Generator[ExecutionContext, None, None]:
    """
    Context manager for binding a cryptographically verified identity & delegated authority to execution scope.
    Usage:
        with guardwaf.verified_session(principal=v_principal, agent=agent_id, authority=del_auth):
            agent.run()
    """
    sess_id = session_id or f"sess_{uuid.uuid4().hex[:10]}"
    t_id = tenant_id or principal.tenant_id

    metadata = {}
    if customer_id:
        metadata["customer_id"] = customer_id

    ctx = ExecutionContext(
        principal=principal,
        agent=agent,
        authority=authority,
        session_id=sess_id,
        tenant_id=t_id,
        metadata=metadata,
    )

    token_exec = _CURRENT_EXECUTION_CONTEXT.set(ctx)
    token_sess = _CURRENT_SESSION.set(ctx.to_legacy_session_context())

    try:
        yield ctx
    finally:
        _CURRENT_EXECUTION_CONTEXT.reset(token_exec)
        _CURRENT_SESSION.reset(token_sess)


@contextmanager
def session(
    session_id: str,
    principal_id: Optional[str] = None,
    customer_id: Optional[str] = None,
    tenant_id: Optional[str] = "default",
    user_role: Optional[str] = "user",
    allowed_scope_ids: Optional[List[str]] = None,
    session_context: Optional[SessionContext] = None,
) -> Generator[SessionContext, None, None]:
    """
    Legacy context manager for development and testing.
    Note: Does not perform cryptographic JWT/OIDC authentication.
    """
    if session_context:
        ctx = session_context
    else:
        ctx = SessionContext(
            session_id=session_id,
            principal_id=principal_id,
            customer_id=customer_id,
            tenant_id=tenant_id,
            user_role=user_role,
            allowed_scope_ids=allowed_scope_ids or [],
        )

    # Construct unverified dev ExecutionContext
    unverified_principal = (
        VerifiedPrincipal(
            principal_id=principal_id or customer_id or "unverified_dev_user",
            tenant_id=tenant_id or "default",
            subject=principal_id or customer_id or "unverified_dev_user",
            authentication_method="static_unverified",
            roles=[user_role or "user"],
        )
        if (principal_id or customer_id)
        else None
    )

    dev_exec_ctx = ExecutionContext(
        principal=unverified_principal,
        session_id=session_id,
        tenant_id=tenant_id or "default",
        metadata={"customer_id": customer_id} if customer_id else {},
    )

    token_exec = _CURRENT_EXECUTION_CONTEXT.set(dev_exec_ctx)
    token_sess = _CURRENT_SESSION.set(ctx)

    try:
        yield ctx
    finally:
        _CURRENT_EXECUTION_CONTEXT.reset(token_exec)
        _CURRENT_SESSION.reset(token_sess)
