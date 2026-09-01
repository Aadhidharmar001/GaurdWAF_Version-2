"""
Cryptographic Key Management & Production Key Rotation Module.
Provides secure secret key resolution, environment checks, and multi-key keyring management.
"""

import os
from typing import Dict, Optional, Tuple

from guardwaf.exceptions import GuardWAFConfigurationError

DEFAULT_DEV_KEY = "gw_secret_default_development_key"


class KeyManager:
    """
    Manages secret keys and keyring dictionaries for signing and verifying Action Grants and HITL tokens.
    Supports key rotation via key_ids (e.g., 'k1', 'k2').
    """

    def __init__(
        self,
        secret_key: Optional[str] = None,
        key_id: str = "k1",
        keyring: Optional[Dict[str, str]] = None,
        environment: Optional[str] = None,
    ):
        self.active_key_id = key_id
        env = (
            environment
            or os.getenv("GUARDWAF_ENV")
            or os.getenv("ENVIRONMENT")
            or "development"
        ).lower()

        # 1. Resolve primary secret key
        resolved_primary = secret_key or os.getenv("GUARDWAF_SECRET_KEY")

        # 2. Production Fail-Fast Enforcement
        if env == "production":
            if not resolved_primary or resolved_primary == DEFAULT_DEV_KEY:
                raise GuardWAFConfigurationError(
                    "CRITICAL SECURITY ERROR: GUARDWAF_SECRET_KEY environment variable or explicit secret_key "
                    "is required in production environment. Refusing to initialize with default development key."
                )

        primary_key = resolved_primary or DEFAULT_DEV_KEY

        # 3. Construct Keyring
        self._keyring: Dict[str, bytes] = {}

        if keyring:
            for k_id, k_val in keyring.items():
                self._keyring[k_id] = k_val.encode("utf-8")

        # Ensure active key_id is registered in keyring
        self._keyring[self.active_key_id] = primary_key.encode("utf-8")

    def get_active_key(self) -> Tuple[str, bytes]:
        """Returns (active_key_id, secret_key_bytes)."""
        return self.active_key_id, self._keyring[self.active_key_id]

    def get_key(self, key_id: str) -> Optional[bytes]:
        """Looks up a secret key by key_id from the keyring."""
        return self._keyring.get(key_id)

    def rotate_key(self, new_key_id: str, new_secret_key: str) -> None:
        """Rotates active signing key to a new key_id while maintaining backward keyring lookup."""
        self._keyring[new_key_id] = new_secret_key.encode("utf-8")
        self.active_key_id = new_key_id
