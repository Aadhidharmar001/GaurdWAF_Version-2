"""
JWT Token Generation, Verification, Password Hashing, and Security Context Manager.
"""

import base64
import hashlib
import hmac
import json
import os
import time
from typing import Any, Dict

from guardwaf.exceptions import GuardWAFSecurityError

# Default secret key or fail-fast check
DEFAULT_SECRET = os.getenv("GUARDWAF_SECRET_KEY", "prod_master_secret_key_phase5a_secure_998877")


def hash_password(password: str) -> str:
    """Computes PBKDF2-HMAC-SHA256 password hash."""
    salt = b"guardwaf_secure_salt_v1"
    return hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100000).hex()


def verify_password(password: str, hashed: str) -> bool:
    """Verifies password against PBKDF2-HMAC-SHA256 hash."""
    return hmac.compare_digest(hash_password(password), hashed)


def create_jwt_token(
    user_id: str,
    email: str,
    organization_id: str,
    role: str,
    expires_in_seconds: int = 86400,
    secret_key: str = DEFAULT_SECRET,
) -> str:
    """Creates signed JWT token with payload."""
    header = {"alg": "HS256", "typ": "JWT"}
    now = int(time.time())
    payload = {
        "sub": user_id,
        "email": email,
        "org_id": organization_id,
        "role": role,
        "iat": now,
        "exp": now + expires_in_seconds,
    }

    h_bytes = base64.urlsafe_b64encode(json.dumps(header).encode("utf-8")).rstrip(b"=")
    p_bytes = base64.urlsafe_b64encode(json.dumps(payload).encode("utf-8")).rstrip(b"=")
    signing_input = h_bytes + b"." + p_bytes

    sig = hmac.new(secret_key.encode("utf-8"), signing_input, hashlib.sha256).digest()
    sig_bytes = base64.urlsafe_b64encode(sig).rstrip(b"=")

    return (signing_input + b"." + sig_bytes).decode("utf-8")


def verify_jwt_token(token: str, secret_key: str = DEFAULT_SECRET) -> Dict[str, Any]:
    """Verifies JWT token signature and expiration. Returns payload dict."""
    try:
        parts = token.split(".")
        if len(parts) != 3:
            raise GuardWAFSecurityError("Malformed JWT token format.", tool_name="jwt_auth")

        signing_input = (parts[0] + "." + parts[1]).encode("utf-8")
        expected_sig = hmac.new(secret_key.encode("utf-8"), signing_input, hashlib.sha256).digest()

        # Pad signature back
        sig_str = parts[2]
        rem = len(sig_str) % 4
        if rem > 0:
            sig_str += "=" * (4 - rem)
        provided_sig = base64.urlsafe_b64decode(sig_str.encode("utf-8"))

        if not hmac.compare_digest(expected_sig, provided_sig):
            raise GuardWAFSecurityError("Invalid JWT signature.", tool_name="jwt_auth")

        # Decode payload
        payload_str = parts[1]
        rem_p = len(payload_str) % 4
        if rem_p > 0:
            payload_str += "=" * (4 - rem_p)
        payload = json.loads(base64.urlsafe_b64decode(payload_str.encode("utf-8")).decode("utf-8"))

        if payload.get("exp", 0) < time.time():
            raise GuardWAFSecurityError("Expired JWT session token.", tool_name="jwt_auth")

        return payload
    except Exception as e:
        if isinstance(e, GuardWAFSecurityError):
            raise e
        raise GuardWAFSecurityError(f"JWT Verification Failed: {e}", tool_name="jwt_auth")
