"""
IdentityProvider Abstract Base Class.
"""

from abc import ABC, abstractmethod

from guardwaf.identity.models import IdentityCredentials, VerifiedPrincipal


class IdentityProvider(ABC):
    """
    Abstract Base Class for all GuardWAF Identity Providers.
    Authenticates incoming credentials and returns a VerifiedPrincipal.
    """

    @abstractmethod
    def authenticate(self, credentials: IdentityCredentials) -> VerifiedPrincipal:
        """
        Authenticates credentials and produces an immutable VerifiedPrincipal.
        Raises GuardWAFAuthenticationError or GuardWAFInvalidTokenError on failure.
        """
