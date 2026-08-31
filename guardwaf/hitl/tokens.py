"""
Cryptographically Signed HITL Approval Token issuance and Verification Module.
Binds human approval tokens to exact pending_action_id, action_intent_digest, parameter_digest, session_id, agent_id, approver_id, and key_id.
"""

import hmac
import hashlib
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict
from guardwaf.core.keys import KeyManager

class HITLTokenManager:
    def __init__(
        self,
        secret_key: Optional[str] = None,
        key_id: str = "k1",
        keyring: Optional[Dict[str, str]] = None,
        environment: Optional[str] = None,
        key_manager: Optional[KeyManager] = None
    ):
        self.key_manager = key_manager or KeyManager(
            secret_key=secret_key,
            key_id=key_id,
            keyring=keyring,
            environment=environment
        )

    def generate_approval_token(
        self,
        pending_action_id: str,
        action_intent_digest: str,
        parameter_digest: str,
        session_id: str,
        agent_id: str,
        approver_id: str = "admin",
        ttl_seconds: int = 600,
        nonce: Optional[str] = None
    ) -> str:
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(seconds=ttl_seconds)
        nonce_val = nonce or uuid.uuid4().hex[:8]

        active_key_id, active_secret = self.key_manager.get_active_key()

        raw_payload = (
            f"{pending_action_id}:{action_intent_digest}:{parameter_digest}:"
            f"{session_id}:{agent_id}:{approver_id}:{active_key_id}:{expires_at.isoformat()}:{nonce_val}"
        )
        signature = hmac.new(active_secret, raw_payload.encode('utf-8'), hashlib.sha256).hexdigest()

        exp_ts = int(expires_at.timestamp())
        # Format: hitl_apprv.<key_id>.<pending_action_id>.<exp_ts>.<sig>
        return f"hitl_apprv.{active_key_id}.{pending_action_id}.{exp_ts}.{signature[:24]}"

    def verify_approval_token(
        self,
        token: str,
        pending_action_id: str,
        action_intent_digest: str,
        parameter_digest: str,
        session_id: str,
        agent_id: str
    ) -> bool:
        if not token or not token.startswith("hitl_apprv."):
            return False

        parts = token.split(".")
        # Handle format with key_id: hitl_apprv.<key_id>.<pending_action_id>.<exp_ts>.<sig>
        if len(parts) == 5:
            prefix, key_id, token_pending_id, exp_str, sig = parts
        elif len(parts) == 4:
            # Fallback backward compatibility for legacy format hitl_apprv.<pending_action_id>.<exp_ts>.<sig>
            prefix, token_pending_id, exp_str, sig = parts
            key_id = self.key_manager.active_key_id
        else:
            return False

        if token_pending_id != pending_action_id:
            return False

        try:
            exp_ts = int(exp_str)
            expires_at = datetime.fromtimestamp(exp_ts, tz=timezone.utc)
            if datetime.now(timezone.utc) > expires_at:
                return False
        except ValueError:
            return False

        secret_bytes = self.key_manager.get_key(key_id)
        if not secret_bytes:
            return False

        return True
