"""
SDK Policy Client with Background Periodic Refresh, Signed Bundle Verification,
Multi-Tier Local Memory / LKG Caching, and Zero-Latency Hot-Path Enforcement (< 1ms).
"""

import time
import threading
import json
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any, Callable
from guardwaf.control_plane.models.bundle import SignedPolicyBundle
from guardwaf.control_plane.services.bundle_service import BundleService
from guardwaf.core.models import PolicyConfig
from guardwaf.core.policy import parse_policy_dict
from guardwaf.core.keys import KeyManager
from guardwaf.exceptions import GuardWAFSecurityError, GuardWAFConfigurationError

class PolicyClientMode:
    STRICT = "STRICT"
    GRACE_PERIOD = "GRACE_PERIOD"
    DEVELOPMENT = "DEVELOPMENT"

class PolicyClient:
    """
    High-speed SDK Policy Client for local in-process enforcement (< 1ms target).
    Fetches, cryptographically verifies, and atomically caches signed policy bundles from the Control Plane.
    Never performs synchronous network calls in the tool execution hot path.
    """
    def __init__(
        self,
        tenant_id: str = "default",
        agent_id: str = "default_agent",
        environment: str = "production",
        bundle_fetcher: Optional[Callable[[], SignedPolicyBundle]] = None,
        bundle_service: Optional[BundleService] = None,
        key_manager: Optional[KeyManager] = None,
        mode: str = PolicyClientMode.GRACE_PERIOD,
        refresh_interval_seconds: int = 60,
        grace_period_seconds: int = 86400,
        initial_policy: Optional[PolicyConfig] = None
    ):
        self.tenant_id = tenant_id
        self.agent_id = agent_id
        self.environment = environment
        self.bundle_fetcher = bundle_fetcher
        self.bundle_service = bundle_service
        self.key_manager = key_manager or KeyManager()
        self.mode = mode
        self.refresh_interval = refresh_interval_seconds
        self.grace_period_seconds = grace_period_seconds

        self._lock = threading.Lock()
        self._active_bundle: Optional[SignedPolicyBundle] = None
        self._lkg_bundle: Optional[SignedPolicyBundle] = None
        self._active_policy_config: Optional[PolicyConfig] = initial_policy
        self._lkg_policy_config: Optional[PolicyConfig] = initial_policy
        self._last_successful_fetch: float = time.time() if initial_policy else 0.0

        self._refresh_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()

    def set_bundle_fetcher(self, fetcher: Callable[[], SignedPolicyBundle]) -> None:
        self.bundle_fetcher = fetcher

    def verify_and_apply_bundle(self, bundle: SignedPolicyBundle) -> bool:
        """
        Verifies signature, expiration, digest, tenant_id, and agent_id binding.
        Atomically applies valid bundle or retains LKG policy if invalid/tampered.
        """
        with self._lock:
            # 1. Tenant & Agent Binding Check
            if bundle.tenant_id != self.tenant_id:
                print(f"⚠️ [GuardWAF PolicyClient] Rejected bundle: Tenant mismatch ('{bundle.tenant_id}' != '{self.tenant_id}')")
                return False
            if bundle.agent_id != self.agent_id:
                print(f"⚠️ [GuardWAF PolicyClient] Rejected bundle: Agent mismatch ('{bundle.agent_id}' != '{self.agent_id}')")
                return False

            # 2. Cryptographic Signature & SHA-256 Digest Verification
            if self.bundle_service:
                valid_sig = self.bundle_service.verify_bundle_signature(bundle)
            else:
                # Local verification fallback
                valid_sig = self._verify_bundle_signature_local(bundle)

            if not valid_sig:
                print(f"⚠️ [GuardWAF PolicyClient] REJECTED TAMPERED BUNDLE '{bundle.bundle_id}'. Retaining Last Known Good policy.")
                return False

            # 3. Compile PolicyConfig instance
            try:
                new_config = parse_policy_dict(bundle.policy_payload)
            except Exception as e:
                print(f"⚠️ [GuardWAF PolicyClient] Failed to parse bundle policy payload: {e}")
                return False

            # 4. Atomic Swap
            self._active_bundle = bundle
            self._lkg_bundle = bundle
            self._active_policy_config = new_config
            self._lkg_policy_config = new_config
            self._last_successful_fetch = time.time()
            return True

    def _verify_bundle_signature_local(self, bundle: SignedPolicyBundle) -> bool:
        if bundle.is_expired():
            return False
        secret_bytes = self.key_manager.get_key(bundle.key_id)
        if not secret_bytes:
            return False

        # Digest verification
        payload_json = json.dumps(bundle.policy_payload, sort_keys=True)
        expected_digest = hashlib.sha256(payload_json.encode('utf-8')).hexdigest()
        if expected_digest != bundle.bundle_digest:
            return False

        signature_payload = f"{bundle.bundle_id}:{bundle.tenant_id}:{bundle.agent_id}:{bundle.environment}:{bundle.bundle_digest}:{bundle.key_id}:{bundle.issued_at.isoformat()}:{bundle.expires_at.isoformat()}"
        expected_sig = hmac.new(secret_bytes, signature_payload.encode('utf-8'), hashlib.sha256).hexdigest()
        return hmac.compare_digest(bundle.signature, expected_sig)

    def fetch_and_apply_remote(self) -> bool:
        """Fetches bundle from remote control plane/fetcher and applies it."""
        if not self.bundle_fetcher and not self.bundle_service:
            return False

        try:
            if self.bundle_fetcher:
                bundle = self.bundle_fetcher()
            else:
                bundle = self.bundle_service.compile_and_sign_bundle(
                    tenant_id=self.tenant_id,
                    agent_id=self.agent_id,
                    environment=self.environment
                )
            return self.verify_and_apply_bundle(bundle)
        except Exception as err:
            print(f"⚠️ [GuardWAF PolicyClient] Remote fetch failed ({err}). Retaining Last Known Good policy.")
            return False

    def start_background_refresh(self) -> None:
        """Spawns background thread for periodic policy bundle refresh."""
        if self._refresh_thread and self._refresh_thread.is_alive():
            return

        self._stop_event.clear()
        def _loop():
            while not self._stop_event.is_set():
                self.fetch_and_apply_remote()
                self._stop_event.wait(timeout=self.refresh_interval)

        self._refresh_thread = threading.Thread(target=_loop, daemon=True, name="GuardWAFPolicyRefresh")
        self._refresh_thread.start()

    def stop_background_refresh(self) -> None:
        self._stop_event.set()
        if self._refresh_thread and self._refresh_thread.is_alive():
            self._refresh_thread.join(timeout=2.0)

    def get_active_policy(self) -> Optional[PolicyConfig]:
        """
        LOCAL HOT-PATH METHOD (< 1ms target).
        Returns active in-memory PolicyConfig with zero network requests.
        Handles LKG fallback and strict expiration checks.
        """
        with self._lock:
            now_ts = time.time()

            # 1. Check if active bundle is present and unexpired
            if self._active_bundle and not self._active_bundle.is_expired():
                return self._active_policy_config

            # 2. Handle Expired Bundle / Fallback
            if self.mode == PolicyClientMode.STRICT:
                if self.environment == "production":
                    if not self._active_policy_config:
                        raise GuardWAFSecurityError(
                            "CRITICAL: No valid signed policy bundle available in production STRICT mode. Failing closed.",
                            tool_name="policy_client"
                        )
                    if self._active_bundle and self._active_bundle.is_expired():
                        raise GuardWAFSecurityError(
                            "CRITICAL: Signed policy bundle has EXPIRED in production STRICT mode. Failing closed.",
                            tool_name="policy_client"
                        )

            elif self.mode == PolicyClientMode.GRACE_PERIOD:
                # Check if within grace period
                time_since_fetch = now_ts - self._last_successful_fetch
                if time_since_fetch <= self.grace_period_seconds:
                    return self._lkg_policy_config
                elif self.environment == "production":
                    raise GuardWAFSecurityError(
                        f"CRITICAL: Policy grace period ({self.grace_period_seconds}s) exceeded. Failing closed in production.",
                        tool_name="policy_client"
                    )

            return self._active_policy_config or self._lkg_policy_config
