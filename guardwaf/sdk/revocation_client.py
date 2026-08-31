"""
SDK Real-Time Revocation Client with Cryptographic Event Verification,
Monotonic Sequence Validation, Revocation Freshness SLA, and Local O(1) Hot-Path Kill Switches.
"""

import time
import threading
from typing import Optional, Set, Dict, Any, Callable
from guardwaf.control_plane.events.events import (
    SignedRevocationEvent,
    EventSignatureVerifier,
    EventSequenceValidator
)
from guardwaf.core.keys import KeyManager
from guardwaf.exceptions import GuardWAFSecurityError

class RevocationClient:
    """
    Local SDK Revocation Client managing real-time agent/tenant kill switches.
    Checks revocation state locally in O(1) constant time without Control Plane HTTP requests in the hot path.
    """
    def __init__(
        self,
        key_manager: Optional[KeyManager] = None,
        freshness_sla_seconds: int = 300,
        mode: str = "GRACE_PERIOD"  # "STRICT", "GRACE_PERIOD", "DEVELOPMENT"
    ):
        self.key_manager = key_manager or KeyManager()
        self.verifier = EventSignatureVerifier(key_manager=self.key_manager)
        self.sequence_validator = EventSequenceValidator()
        self.freshness_sla_seconds = freshness_sla_seconds
        self.mode = mode

        self._lock = threading.Lock()
        self._revoked_agents: Set[str] = set()
        self._locked_tenants: Set[str] = set()
        self._revoked_authorities: Set[str] = set()
        self._last_event_time: float = time.time()

    def process_signed_event(self, event: SignedRevocationEvent) -> bool:
        """
        Verifies HMAC signature & sequence number before applying revocation event to local cache.
        """
        with self._lock:
            # 1. Cryptographic Signature Verification
            if not self.verifier.verify_event_signature(event):
                print(f"⚠️ [GuardWAF RevocationClient] REJECTED EVENT {event.event_id}: Invalid cryptographic signature.")
                return False

            # 2. Sequence Validation (Anti-Replay / Monotonic Order)
            if not self.sequence_validator.is_valid_sequence(event.tenant_id, event.sequence_number, event.agent_id):
                print(f"⚠️ [GuardWAF RevocationClient] REJECTED EVENT {event.event_id}: Stale sequence number ({event.sequence_number}).")
                return False

            # 3. Apply Revocation State
            if event.event_type == "AGENT_REVOKED" and event.agent_id:
                self._revoked_agents.add(event.agent_id)
            elif event.event_type == "TENANT_LOCKDOWN":
                self._locked_tenants.add(event.tenant_id)
            elif event.event_type == "AUTHORITY_REVOKED" and event.agent_id:
                self._revoked_authorities.add(event.agent_id)

            self._last_event_time = time.time()
            return True

    def revoke_agent_local(self, agent_id: str) -> None:
        """Local direct agent revocation helper for testing / emergency shutdown."""
        with self._lock:
            self._revoked_agents.add(agent_id)
            self._last_event_time = time.time()

    def lockdown_tenant_local(self, tenant_id: str) -> None:
        """Local direct tenant emergency lockdown helper."""
        with self._lock:
            self._locked_tenants.add(tenant_id)
            self._last_event_time = time.time()

    def check_kill_switch_local(self, tenant_id: str, agent_id: str) -> None:
        """
        LOCAL HOT-PATH METHOD (O(1) in-memory check).
        Executed before any tool call or policy evaluation.
        Zero Control Plane network calls.
        """
        with self._lock:
            # 1. Check Tenant Emergency Lockdown
            if tenant_id in self._locked_tenants:
                raise GuardWAFSecurityError(
                    f"CRITICAL: Tenant '{tenant_id}' is under EMERGENCY LOCKDOWN. Action denied.",
                    tool_name="kill_switch"
                )

            # 2. Check Agent Revocation
            if agent_id in self._revoked_agents:
                raise GuardWAFSecurityError(
                    f"CRITICAL: Agent '{agent_id}' has been REVOKED. Action denied.",
                    tool_name="kill_switch"
                )

            # 3. Check Revocation Freshness SLA
            time_since_sync = time.time() - self._last_event_time
            if time_since_sync > self.freshness_sla_seconds:
                if self.mode == "STRICT":
                    raise GuardWAFSecurityError(
                        f"CRITICAL: Revocation freshness SLA ({self.freshness_sla_seconds}s) exceeded. Failing closed in STRICT mode.",
                        tool_name="kill_switch"
                    )
