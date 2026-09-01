"""
GuardWAF — Action Authorization & Runtime Governance Platform for Autonomous AI Systems.
"""

from guardwaf.core.authority import DelegatedAuthority
from guardwaf.core.models import ActionGrant, ActionIntent, ActionState, PendingAction
from guardwaf.exceptions import (
    GuardWAFActionExpiredError,
    GuardWAFAlreadyExecutedError,
    GuardWAFAuthenticationError,
    GuardWAFAuthorityExpiredError,
    GuardWAFAuthorizationError,
    GuardWAFConfigurationError,
    GuardWAFException,
    GuardWAFHITLRequiredError,
    GuardWAFIdentityError,
    GuardWAFInvalidStateTransitionError,
    GuardWAFInvalidTokenError,
    GuardWAFSecurityError,
    GuardWAFTenantBoundaryError,
    GuardWAFUnverifiedContextError,
)
from guardwaf.identity import (
    AgentIdentity,
    IdentityCredentials,
    IdentityProvider,
    JWTIdentityProvider,
    OIDCIdentityProvider,
    StaticIdentityProvider,
    VerifiedPrincipal,
)
from guardwaf.sdk.client import GuardWAF
from guardwaf.sdk.context import (
    ExecutionContext,
    get_current_execution_context,
    get_current_session,
    session,
    verified_session,
)
from guardwaf.sdk.decorators import protect
from guardwaf.state.base import StateStore
from guardwaf.state.memory import MemoryStateStore
from guardwaf.state.redis import RedisStateStore
from guardwaf.state.sqlite import SQLiteStateStore

__version__ = "0.3.0"

__all__ = [
    "ActionGrant",
    "ActionIntent",
    "ActionState",
    "AgentIdentity",
    "DelegatedAuthority",
    "ExecutionContext",
    "GuardWAF",
    "GuardWAFActionExpiredError",
    "GuardWAFAlreadyExecutedError",
    "GuardWAFAuthenticationError",
    "GuardWAFAuthorityExpiredError",
    "GuardWAFAuthorizationError",
    "GuardWAFConfigurationError",
    "GuardWAFException",
    "GuardWAFHITLRequiredError",
    "GuardWAFIdentityError",
    "GuardWAFInvalidStateTransitionError",
    "GuardWAFInvalidTokenError",
    "GuardWAFSecurityError",
    "GuardWAFTenantBoundaryError",
    "GuardWAFUnverifiedContextError",
    "IdentityCredentials",
    "IdentityProvider",
    "JWTIdentityProvider",
    "MemoryStateStore",
    "OIDCIdentityProvider",
    "PendingAction",
    "RedisStateStore",
    "SQLiteStateStore",
    "StateStore",
    "StaticIdentityProvider",
    "VerifiedPrincipal",
    "get_current_execution_context",
    "get_current_session",
    "protect",
    "session",
    "verified_session",
]
