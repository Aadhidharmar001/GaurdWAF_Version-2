"""
GuardWAF — Action Authorization & Runtime Governance Platform for Autonomous AI Systems.
"""

from guardwaf.sdk.client import GuardWAF
from guardwaf.sdk.context import (
    session,
    verified_session,
    get_current_session,
    get_current_execution_context,
    ExecutionContext,
)
from guardwaf.sdk.decorators import protect
from guardwaf.core.models import ActionState, PendingAction, ActionIntent, ActionGrant
from guardwaf.core.authority import DelegatedAuthority
from guardwaf.identity import (
    VerifiedPrincipal,
    AgentIdentity,
    IdentityCredentials,
    IdentityProvider,
    StaticIdentityProvider,
    JWTIdentityProvider,
    OIDCIdentityProvider,
)
from guardwaf.state.base import StateStore
from guardwaf.state.memory import MemoryStateStore
from guardwaf.state.sqlite import SQLiteStateStore
from guardwaf.state.redis import RedisStateStore
from guardwaf.exceptions import (
    GuardWAFException,
    GuardWAFSecurityError,
    GuardWAFHITLRequiredError,
    GuardWAFConfigurationError,
    GuardWAFInvalidStateTransitionError,
    GuardWAFActionExpiredError,
    GuardWAFAlreadyExecutedError,
    GuardWAFIdentityError,
    GuardWAFAuthenticationError,
    GuardWAFAuthorizationError,
    GuardWAFAuthorityExpiredError,
    GuardWAFTenantBoundaryError,
    GuardWAFInvalidTokenError,
    GuardWAFUnverifiedContextError,
)

__version__ = "0.3.0"

__all__ = [
    "GuardWAF",
    "session",
    "verified_session",
    "get_current_session",
    "get_current_execution_context",
    "ExecutionContext",
    "protect",
    "ActionState",
    "PendingAction",
    "ActionIntent",
    "ActionGrant",
    "DelegatedAuthority",
    "VerifiedPrincipal",
    "AgentIdentity",
    "IdentityCredentials",
    "IdentityProvider",
    "StaticIdentityProvider",
    "JWTIdentityProvider",
    "OIDCIdentityProvider",
    "StateStore",
    "MemoryStateStore",
    "SQLiteStateStore",
    "RedisStateStore",
    "GuardWAFException",
    "GuardWAFSecurityError",
    "GuardWAFHITLRequiredError",
    "GuardWAFConfigurationError",
    "GuardWAFInvalidStateTransitionError",
    "GuardWAFActionExpiredError",
    "GuardWAFAlreadyExecutedError",
    "GuardWAFIdentityError",
    "GuardWAFAuthenticationError",
    "GuardWAFAuthorizationError",
    "GuardWAFAuthorityExpiredError",
    "GuardWAFTenantBoundaryError",
    "GuardWAFInvalidTokenError",
    "GuardWAFUnverifiedContextError",
]
