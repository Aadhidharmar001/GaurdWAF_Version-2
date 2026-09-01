"""
GuardWAF Exception Hierarchy with Machine-Readable Error Codes.
"""

from typing import Optional


class GuardWAFException(Exception):
    """Base exception for all GuardWAF errors."""

    def __init__(self, message: str, code: Optional[str] = None):
        super().__init__(message)
        self.message = message
        self.code = code or self.__class__.__name__


class GuardWAFConfigurationError(GuardWAFException):
    """Raised when configuration or policy loading fails."""


class GuardWAFSecurityError(GuardWAFException):
    """
    Raised when an action is blocked by a GuardWAF policy.
    The protected function body is NEVER executed when this exception is raised.
    """

    def __init__(
        self,
        message: str,
        tool_name: str,
        matched_rule: Optional[str] = None,
        details: Optional[dict] = None,
        code: Optional[str] = None,
    ):
        super().__init__(message, code=code or "SECURITY_VIOLATION")
        self.tool_name = tool_name
        self.matched_rule = matched_rule
        self.details = details or {}


class GuardWAFHITLRequiredError(GuardWAFException):
    """
    Raised when an action requires Human-in-the-Loop approval before proceeding.
    Contains the pending_action_id and approval token.
    """

    def __init__(
        self,
        message: str,
        pending_action_id: str,
        tool_name: str,
        approval_token: Optional[str] = None,
        hitl_id: Optional[str] = None,
        details: Optional[dict] = None,
    ):
        super().__init__(message, code="HITL_APPROVAL_REQUIRED")
        self.pending_action_id = pending_action_id
        self.hitl_id = hitl_id or pending_action_id
        self.tool_name = tool_name
        self.approval_token = approval_token
        self.details = details or {}


class GuardWAFInvalidStateTransitionError(GuardWAFException):
    """Raised when an illegal HITL state machine transition is attempted."""

    def __init__(self, message: str):
        super().__init__(message, code="INVALID_STATE_TRANSITION")


class GuardWAFActionExpiredError(GuardWAFException):
    """Raised when attempting to approve or execute an expired pending action."""

    def __init__(self, message: str):
        super().__init__(message, code="ACTION_EXPIRED")


class GuardWAFAlreadyExecutedError(GuardWAFSecurityError):
    """Raised when an action has already been executed (prevents double execution)."""

    def __init__(self, message: str, tool_name: str, pending_action_id: str):
        super().__init__(
            message,
            tool_name=tool_name,
            matched_rule="idempotency_check",
            code="ALREADY_EXECUTED",
        )
        self.pending_action_id = pending_action_id


# --- Phase 3A Structured Identity & Delegated Authority Exceptions ---


class GuardWAFIdentityError(GuardWAFSecurityError):
    """Base error for identity verification failures."""

    def __init__(
        self,
        message: str,
        tool_name: str = "identity_verification",
        code: str = "IDENTITY_ERROR",
    ):
        super().__init__(message, tool_name=tool_name, code=code)


class GuardWAFAuthenticationError(GuardWAFIdentityError):
    """Raised when identity authentication fails (invalid token, bad signature, etc)."""

    def __init__(self, message: str, code: str = "AUTHENTICATION_FAILED"):
        super().__init__(message, code=code)


class GuardWAFInvalidTokenError(GuardWAFAuthenticationError):
    """Raised when a JWT or OAuth token is malformed, forged, or unparseable."""

    def __init__(self, message: str, code: str = "INVALID_TOKEN"):
        super().__init__(message, code=code)


class GuardWAFAuthorizationError(GuardWAFIdentityError):
    """Raised when an authenticated principal or agent lacks delegated authority for an action."""

    def __init__(
        self,
        message: str,
        tool_name: str = "unknown",
        code: str = "AUTHORIZATION_DENIED",
    ):
        super().__init__(message, tool_name=tool_name, code=code)


class GuardWAFAuthorityExpiredError(GuardWAFAuthorizationError):
    """Raised when a DelegatedAuthority token or grant has expired."""

    def __init__(self, message: str, tool_name: str = "unknown"):
        super().__init__(message, tool_name=tool_name, code="AUTHORITY_EXPIRED")


class GuardWAFTenantBoundaryError(GuardWAFAuthorizationError):
    """Raised when an action attempts to cross tenant boundaries or spoof tenant context."""

    def __init__(self, message: str, tool_name: str = "unknown"):
        super().__init__(message, tool_name=tool_name, code="TENANT_BOUNDARY_VIOLATION")


class GuardWAFUnverifiedContextError(GuardWAFIdentityError):
    """Raised in strict production mode when an action runs without a VerifiedPrincipal context."""

    def __init__(
        self,
        message: str = "Action executed without a cryptographically verified principal context.",
    ):
        super().__init__(message, code="UNVERIFIED_IDENTITY_CONTEXT")
