"""
OIDC Identity Provider with JWKS key lookup and TTL caching support.
Extends JWTIdentityProvider for enterprise identity management (Okta, Auth0, Entra ID, Cognito).
"""

import time
from typing import Callable, Dict, Optional

import jwt

from guardwaf.exceptions import GuardWAFInvalidTokenError
from guardwaf.identity.jwt import JWTIdentityProvider
from guardwaf.identity.models import IdentityCredentials, VerifiedPrincipal


class OIDCIdentityProvider(JWTIdentityProvider):
    def __init__(
        self,
        issuer: str,
        audience: str,
        jwks_keys: Optional[Dict[str, str]] = None,
        jwks_fetcher: Optional[Callable[[str], Dict[str, str]]] = None,
        cache_ttl_seconds: int = 3600,
        principal_id_claim: str = "sub",
        tenant_id_claim: str = "tenant_id",
    ):
        super().__init__(
            issuer=issuer,
            audience=audience,
            algorithms=["RS256"],
            principal_id_claim=principal_id_claim,
            tenant_id_claim=tenant_id_claim,
        )
        self.jwks_fetcher = jwks_fetcher
        self.cache_ttl = cache_ttl_seconds
        self._key_cache: Dict[str, str] = jwks_keys or {}
        self._last_fetch_time: float = time.time() if jwks_keys else 0.0

    def _resolve_jwks_key(self, kid: str) -> str:
        now = time.time()
        # Check cache
        if kid in self._key_cache and (now - self._last_fetch_time) < self.cache_ttl:
            return self._key_cache[kid]

        # Fetch fresh JWKS keys if fetcher function is provided
        if self.jwks_fetcher:
            fresh_keys = self.jwks_fetcher(kid)
            self._key_cache.update(fresh_keys)
            self._last_fetch_time = now

        if kid not in self._key_cache:
            raise GuardWAFInvalidTokenError(
                f"JWKS Key ID '{kid}' not found in OIDC provider public key set."
            )

        return self._key_cache[kid]

    def authenticate(self, credentials: IdentityCredentials) -> VerifiedPrincipal:
        raw_token = credentials.raw_token
        try:
            header = jwt.get_unverified_header(raw_token)
            kid = header.get("kid")
        except Exception as e:
            raise GuardWAFInvalidTokenError(f"Failed to read OIDC JWT header: {e!s}")

        if not kid and not self._key_cache:
            raise GuardWAFInvalidTokenError(
                "OIDC JWT token missing required 'kid' header field."
            )

        key_id = kid or list(self._key_cache.keys())[0]
        public_key = self._resolve_jwks_key(key_id)

        # Set public key dynamically and delegate verification to superclass
        self.public_key = public_key
        return super().authenticate(credentials)
