"""
Re-exporting Identity Exceptions for module cleanliness.
"""

from guardwaf.exceptions import (
    GuardWAFAuthenticationError,
    GuardWAFAuthorityExpiredError,
    GuardWAFAuthorizationError,
    GuardWAFIdentityError,
    GuardWAFInvalidTokenError,
    GuardWAFTenantBoundaryError,
    GuardWAFUnverifiedContextError,
)

__all__ = [
    "GuardWAFAuthenticationError",
    "GuardWAFAuthorityExpiredError",
    "GuardWAFAuthorizationError",
    "GuardWAFIdentityError",
    "GuardWAFInvalidTokenError",
    "GuardWAFTenantBoundaryError",
    "GuardWAFUnverifiedContextError",
]
