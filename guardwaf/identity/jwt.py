"""
Cryptographic JWT Identity Provider Implementation.
Verifies JWT signatures, expiration, issuer, audience, and maps claims to VerifiedPrincipal.
Explicitly rejects alg=none and unverified tokens.
"""

import jwt
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from guardwaf.identity.base import IdentityProvider
from guardwaf.identity.models import IdentityCredentials, VerifiedPrincipal
from guardwaf.exceptions import GuardWAFAuthenticationError, GuardWAFInvalidTokenError

class JWTIdentityProvider(IdentityProvider):
    def __init__(
        self,
        secret_key: Optional[str] = None,
        public_key: Optional[str] = None,
        algorithms: Optional[List[str]] = None,
        issuer: Optional[str] = None,
        audience: Optional[str] = None,
        principal_id_claim: str = "sub",
        tenant_id_claim: str = "tenant_id",
        roles_claim: str = "roles",
        permissions_claim: str = "permissions"
    ):
        self.secret_key = secret_key
        self.public_key = public_key
        self.algorithms = algorithms or (["RS256"] if public_key else ["HS256"])
        self.issuer = issuer
        self.audience = audience
        self.principal_id_claim = principal_id_claim
        self.tenant_id_claim = tenant_id_claim
        self.roles_claim = roles_claim
        self.permissions_claim = permissions_claim

    def _get_verification_key(self, token: str):
        if self.public_key:
            return self.public_key
        if self.secret_key:
            return self.secret_key
        raise GuardWAFAuthenticationError("JWTIdentityProvider requires either secret_key or public_key for verification.")

    def authenticate(self, credentials: IdentityCredentials) -> VerifiedPrincipal:
        raw_token = credentials.raw_token
        if not raw_token:
            raise GuardWAFInvalidTokenError("Empty or missing raw_token in IdentityCredentials.")

        # Check for alg=none in unverified header
        try:
            unverified_header = jwt.get_unverified_header(raw_token)
            alg = unverified_header.get("alg", "").lower()
            if alg == "none" or "none" in self.algorithms:
                raise GuardWAFInvalidTokenError("CRITICAL SECURITY ERROR: alg=none JWT tokens are strictly prohibited.")
        except Exception as err:
            if isinstance(err, GuardWAFInvalidTokenError):
                raise err
            raise GuardWAFInvalidTokenError(f"Failed to parse JWT header: {str(err)}")

        key = self._get_verification_key(raw_token)

        options = {
            "verify_signature": True,
            "verify_exp": True,
            "verify_nbf": True,
            "verify_iat": True,
            "verify_aud": bool(self.audience),
            "verify_iss": bool(self.issuer),
        }

        try:
            payload = jwt.decode(
                raw_token,
                key=key,
                algorithms=self.algorithms,
                issuer=self.issuer,
                audience=self.audience,
                options=options
            )
        except jwt.ExpiredSignatureError:
            raise GuardWAFAuthenticationError("JWT signature has expired.")
        except jwt.InvalidIssuerError:
            raise GuardWAFAuthenticationError(f"JWT issuer mismatch. Expected '{self.issuer}'.")
        except jwt.InvalidAudienceError:
            raise GuardWAFAuthenticationError(f"JWT audience mismatch. Expected '{self.audience}'.")
        except jwt.PyJWTError as e:
            raise GuardWAFInvalidTokenError(f"Cryptographic JWT verification failed: {str(e)}")

        # Extract Claims
        principal_id = payload.get(self.principal_id_claim) or payload.get("sub")
        if not principal_id:
            raise GuardWAFInvalidTokenError(f"JWT missing required principal claim '{self.principal_id_claim}'.")

        tenant_id = payload.get(self.tenant_id_claim, "default")
        roles = payload.get(self.roles_claim, [])
        if isinstance(roles, str):
            roles = [roles]

        permissions = payload.get(self.permissions_claim, [])
        if isinstance(permissions, str):
            permissions = [permissions]

        exp_ts = payload.get("exp")
        expires_at = datetime.fromtimestamp(exp_ts, tz=timezone.utc) if exp_ts else None

        iat_ts = payload.get("iat")
        issued_at = datetime.fromtimestamp(iat_ts, tz=timezone.utc) if iat_ts else datetime.now(timezone.utc)

        return VerifiedPrincipal(
            principal_id=str(principal_id),
            tenant_id=str(tenant_id),
            subject=str(payload.get("sub", principal_id)),
            issuer=str(payload.get("iss", self.issuer or "jwt_provider")),
            audience=str(payload.get("aud", self.audience or "guardwaf-api")),
            authentication_method="jwt",
            roles=roles,
            permissions=permissions,
            issued_at=issued_at,
            expires_at=expires_at,
            claims=payload
        )
