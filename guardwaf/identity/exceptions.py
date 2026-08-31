"""
Re-exporting Identity Exceptions for module cleanliness.
"""

from guardwaf.exceptions import (
    GuardWAFIdentityError,
    GuardWAFAuthenticationError,
    GuardWAFInvalidTokenError,
    GuardWAFAuthorizationError,
    GuardWAFAuthorityExpiredError,
    GuardWAFTenantBoundaryError,
    GuardWAFUnverifiedContextError,
)

__all__ = [
    "GuardWAFIdentityError",
    "GuardWAFAuthenticationError",
    "GuardWAFInvalidTokenError",
    "GuardWAFAuthorizationError",
    "GuardWAFAuthorityExpiredError",
    "GuardWAFTenantBoundaryError",
    "GuardWAFUnverifiedContextError",
]
