"""
Static IdentityProvider implementation for tests, local development, and demo harnesses.
MUST NOT silently become the production default.
"""

from typing import Dict
from guardwaf.identity.base import IdentityProvider
from guardwaf.identity.models import IdentityCredentials, VerifiedPrincipal
from guardwaf.exceptions import GuardWAFAuthenticationError

class StaticIdentityProvider(IdentityProvider):
    def __init__(self, principals: Dict[str, VerifiedPrincipal]):
        self._principals = principals

    def register_principal(self, token: str, principal: VerifiedPrincipal) -> None:
        self._principals[token] = principal

    def authenticate(self, credentials: IdentityCredentials) -> VerifiedPrincipal:
        token = credentials.raw_token
        if token not in self._principals:
            raise GuardWAFAuthenticationError(f"Static token '{token[:10]}...' not found in static provider registry.")
        
        principal = self._principals[token]
        if principal.is_expired():
            raise GuardWAFAuthenticationError(f"VerifiedPrincipal '{principal.principal_id}' has expired.")

        return principal
