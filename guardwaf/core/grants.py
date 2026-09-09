"""
Action Authorization Grant (AAG) Issuance and Cryptographic Verification Module.
Includes key_id header binding, principal identity binding, and zero-downtime key rotation support.
"""

import hashlib
import hmac
import uuid
from datetime import datetime, timedelta, timezone
from typing import Dict, Optional

from guardwaf.core.keys import KeyManager
from guardwaf.core.models import ActionGrant, ActionIntent


class GrantSigner:
    """
    Local HMAC Signer for Action Authorization Grants with Key Rotation & Identity Binding Support.
    """

    def __init__(
        self,
        secret_key: Optional[str] = None,
        key_id: str = "k1",
        keyring: Optional[Dict[str, str]] = None,
        environment: Optional[str] = None,
        key_manager: Optional[KeyManager] = None,
    ):
        self.key_manager = key_manager or KeyManager(
            secret_key=secret_key,
            key_id=key_id,
            keyring=keyring,
            environment=environment,
        )

    def issue_grant(
        self,
        intent: ActionIntent,
        ttl_seconds: int = 30,
        policy_version: str = "v1",
        delegated_authority_id: Optional[str] = None,
    ) -> ActionGrant:
        grant_id = f"aag_{uuid.uuid4().hex[:12]}"
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(seconds=ttl_seconds)
        nonce = uuid.uuid4().hex[:8]

        session_id = intent.session_context.session_id if intent.session_context else "default_session"
        principal_id = intent.session_context.principal_id if intent.session_context else None
        tenant_id = intent.session_context.tenant_id if intent.session_context else "default"

        active_key_id, active_secret = self.key_manager.get_active_key()

        payload = f"{grant_id}:{intent.agent_id}:{principal_id or ''}:{tenant_id}:{session_id}:{intent.tool_name}:{intent.parameter_digest}:{delegated_authority_id or ''}:{active_key_id}:{now.isoformat()}:{expires_at.isoformat()}:{nonce}"
        signature = hmac.new(active_secret, payload.encode("utf-8"), hashlib.sha256).hexdigest()

        return ActionGrant(
            grant_id=grant_id,
            issuer="guardwaf-in-process-engine",
            subject_agent=intent.agent_id,
            principal_id=principal_id,
            tenant_id=tenant_id,
            delegated_authority_id=delegated_authority_id,
            session_id=session_id,
            target_action=intent.tool_name,
            parameter_digest=intent.parameter_digest,
            policy_version=policy_version,
            key_id=active_key_id,
            issued_at=now,
            expires_at=expires_at,
            nonce=nonce,
            signature=signature,
        )

    def verify_grant(self, grant: ActionGrant, expected_parameter_digest: str) -> bool:
        # Check expiration
        now = datetime.now(timezone.utc)
        if grant.expires_at < now:
            return False

        # Check parameter digest hash matching
        if grant.parameter_digest != expected_parameter_digest:
            return False

        # Lookup signing key by key_id for key rotation support
        secret_bytes = self.key_manager.get_key(grant.key_id)
        if not secret_bytes:
            return False

        # Verify cryptographic signature
        payload = f"{grant.grant_id}:{grant.subject_agent}:{grant.principal_id or ''}:{grant.tenant_id}:{grant.session_id}:{grant.target_action}:{grant.parameter_digest}:{grant.delegated_authority_id or ''}:{grant.key_id}:{grant.issued_at.isoformat()}:{grant.expires_at.isoformat()}:{grant.nonce}"
        expected_signature = hmac.new(secret_bytes, payload.encode("utf-8"), hashlib.sha256).hexdigest()

        return hmac.compare_digest(grant.signature, expected_signature)
