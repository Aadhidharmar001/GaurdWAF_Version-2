"""
Cryptographically Signed Revocation Events, Signature Verification, and Sequence Validation.
Protects Control Plane -> SDK communication against forgery, tampering, and replay attacks.
"""

import hashlib
import hmac
import uuid
from datetime import datetime, timedelta, timezone
from typing import Dict, Optional

from pydantic import BaseModel, Field

from guardwaf.core.keys import KeyManager


class SignedRevocationEvent(BaseModel):
    """
    Immutable signed revocation event emitted by the Control Plane.
    """

    event_id: str
    event_type: str  # "AGENT_REVOKED", "TENANT_LOCKDOWN", "AUTHORITY_REVOKED"
    tenant_id: str
    agent_id: Optional[str] = None
    issued_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: datetime
    sequence_number: int
    key_id: str = "k1"
    signature: str

    def is_expired(self) -> bool:
        return datetime.now(timezone.utc) > self.expires_at


class EventSignatureVerifier:
    def __init__(self, key_manager: Optional[KeyManager] = None):
        self.key_manager = key_manager or KeyManager()

    def sign_event(
        self,
        event_type: str,
        tenant_id: str,
        sequence_number: int,
        agent_id: Optional[str] = None,
        ttl_seconds: int = 86400,
    ) -> SignedRevocationEvent:
        active_key_id, active_secret = self.key_manager.get_active_key()
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(seconds=ttl_seconds)
        event_id = f"rev_{uuid.uuid4().hex[:10]}"

        signature_payload = f"{event_id}:{event_type}:{tenant_id}:{agent_id or '*'}:{sequence_number}:{active_key_id}:{now.isoformat()}:{expires_at.isoformat()}"
        signature = hmac.new(
            active_secret, signature_payload.encode("utf-8"), hashlib.sha256
        ).hexdigest()

        return SignedRevocationEvent(
            event_id=event_id,
            event_type=event_type,
            tenant_id=tenant_id,
            agent_id=agent_id,
            issued_at=now,
            expires_at=expires_at,
            sequence_number=sequence_number,
            key_id=active_key_id,
            signature=signature,
        )

    def verify_event_signature(self, event: SignedRevocationEvent) -> bool:
        if event.is_expired():
            return False

        secret_bytes = self.key_manager.get_key(event.key_id)
        if not secret_bytes:
            return False

        signature_payload = f"{event.event_id}:{event.event_type}:{event.tenant_id}:{event.agent_id or '*'}:{event.sequence_number}:{event.key_id}:{event.issued_at.isoformat()}:{event.expires_at.isoformat()}"
        expected_sig = hmac.new(
            secret_bytes, signature_payload.encode("utf-8"), hashlib.sha256
        ).hexdigest()

        return hmac.compare_digest(event.signature, expected_sig)


class EventSequenceValidator:
    """
    Validates per-tenant / per-agent monotonic sequence numbers to prevent stale or replayed events.
    """

    def __init__(self):
        self._watermarks: Dict[str, int] = {}

    def is_valid_sequence(
        self, tenant_id: str, sequence_number: int, agent_id: Optional[str] = None
    ) -> bool:
        key = f"{tenant_id}:{agent_id or '*'}"
        last_seq = self._watermarks.get(key, 0)
        if sequence_number <= last_seq:
            return False
        self._watermarks[key] = sequence_number
        return True
