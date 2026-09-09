"""
Agent Credential Lifecycle, Secure Hashing, Verification, and Rotation Service.
"""

import hashlib
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional

from guardwaf.control_plane.models.credential import (
    AgentCredential,
    IssuedCredentialResponse,
)
from guardwaf.exceptions import GuardWAFConfigurationError, GuardWAFSecurityError


class CredentialService:
    def __init__(self):
        self._credentials: Dict[str, AgentCredential] = {}

    def issue_credential(self, organization_id: str, agent_id: str, ttl_days: Optional[int] = None) -> IssuedCredentialResponse:
        cred_id = f"cred_{uuid.uuid4().hex[:10]}"
        raw_key_secret = uuid.uuid4().hex + uuid.uuid4().hex
        plaintext_api_key = f"gw_live_{raw_key_secret}"
        prefix = plaintext_api_key[:12]

        cred_hash = hashlib.sha256(plaintext_api_key.encode("utf-8")).hexdigest()
        now = datetime.now(timezone.utc)

        cred = AgentCredential(
            credential_id=cred_id,
            organization_id=organization_id,
            agent_id=agent_id,
            credential_prefix=prefix,
            credential_hash=cred_hash,
            created_at=now,
        )
        self._credentials[cred_id] = cred

        return IssuedCredentialResponse(
            credential_id=cred_id,
            organization_id=organization_id,
            agent_id=agent_id,
            plaintext_api_key=plaintext_api_key,
            created_at=now,
        )

    def verify_credential(self, plaintext_api_key: str) -> AgentCredential:
        """
        Verifies plaintext API key against SHA-256 hash. Updates last_used_at timestamp.
        """
        provided_hash = hashlib.sha256(plaintext_api_key.encode("utf-8")).hexdigest()

        for cred in self._credentials.values():
            if cred.credential_hash == provided_hash:
                if cred.revoked_at:
                    raise GuardWAFSecurityError("API Credential has been REVOKED.", tool_name="credentials")
                if cred.expires_at and cred.expires_at < datetime.now(timezone.utc):
                    raise GuardWAFSecurityError("API Credential has EXPIRED.", tool_name="credentials")

                cred.last_used_at = datetime.now(timezone.utc)
                return cred

        raise GuardWAFSecurityError("Invalid or unknown API Credential.", tool_name="credentials")

    def revoke_credential(self, credential_id: str) -> AgentCredential:
        cred = self._credentials.get(credential_id)
        if not cred:
            raise GuardWAFConfigurationError(f"Credential '{credential_id}' not found.")

        cred.revoked_at = datetime.now(timezone.utc)
        return cred

    def list_credentials(self, organization_id: str, agent_id: Optional[str] = None) -> List[AgentCredential]:
        results = []
        for cred in self._credentials.values():
            if cred.organization_id == organization_id:
                if agent_id is None or cred.agent_id == agent_id:
                    results.append(cred)
        return results
