"""
Signed Policy Bundle Compilation, Cryptographic Signing, and Verification Service.
"""

import hashlib
import hmac
import json
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from guardwaf.control_plane.models.agent import AgentStatus
from guardwaf.control_plane.models.bundle import SignedPolicyBundle
from guardwaf.control_plane.repositories.base import AgentRepository, PolicyRepository
from guardwaf.control_plane.services.audit_service import AuditService
from guardwaf.control_plane.services.authority_service import AuthorityService
from guardwaf.core.keys import KeyManager
from guardwaf.exceptions import GuardWAFConfigurationError, GuardWAFSecurityError


class BundleService:
    def __init__(
        self,
        agent_repo: AgentRepository,
        policy_repo: PolicyRepository,
        authority_service: Optional[AuthorityService] = None,
        key_manager: Optional[KeyManager] = None,
        audit_service: Optional[AuditService] = None,
    ):
        self.agent_repo = agent_repo
        self.policy_repo = policy_repo
        self.authority_service = authority_service
        self.key_manager = key_manager or KeyManager()
        self.audit_service = audit_service

    def compile_and_sign_bundle(
        self,
        tenant_id: str,
        agent_id: str,
        environment: str = "production",
        ttl_seconds: int = 3600,
    ) -> SignedPolicyBundle:
        # 1. Verify Agent Status
        agent = self.agent_repo.get_agent(agent_id)
        if not agent:
            raise GuardWAFConfigurationError(
                f"Agent '{agent_id}' not found in registry."
            )

        if agent.status == AgentStatus.REVOKED:
            if self.audit_service:
                self.audit_service.record_event(
                    "BUNDLE_REJECTED",
                    tenant_id,
                    "system",
                    "agent",
                    agent_id,
                    {"reason": "Agent REVOKED"},
                )
            raise GuardWAFSecurityError(
                f"Agent '{agent_id}' has been REVOKED. Refusing to issue policy bundle.",
                tool_name="bundle_compiler",
            )

        if agent.tenant_id != tenant_id:
            raise GuardWAFSecurityError(
                f"Tenant mismatch: Agent '{agent_id}' belongs to tenant '{agent.tenant_id}', not '{tenant_id}'.",
                tool_name="bundle_compiler",
            )

        # 2. Resolve Assigned Policies (Precedence: Agent-specific -> Tenant-wide)
        assignments = self.policy_repo.list_assignments(
            tenant_id=tenant_id, agent_id=agent_id, environment=environment
        )
        if not assignments:
            assignments = self.policy_repo.list_assignments(
                tenant_id=tenant_id, agent_id=None, environment=environment
            )

        policy_versions_map: Dict[str, int] = {}
        compiled_rules: Dict[str, List[Any]] = {
            "rate_limits": [],
            "sequences": [],
            "bulk_thresholds": [],
            "data_scope": [],
            "parameter_blocklist": [],
            "hitl_rules": [],
        }

        for ass in assignments:
            pol = self.policy_repo.get_policy(ass.policy_id)
            if not pol or not pol.active_version:
                continue

            ver_num = ass.version_number or pol.active_version
            ver = self.policy_repo.get_policy_version(ass.policy_id, ver_num)
            if not ver:
                continue

            policy_versions_map[pol.name] = ver.version_number
            # Merge rules
            for category, rule_list in ver.rules.items():
                if category in compiled_rules and isinstance(rule_list, list):
                    compiled_rules[category].extend(rule_list)

        policy_payload = {
            "metadata": {
                "policy_name": f"bundle_{tenant_id}_{agent_id}",
                "version": "1.0",
                "description": f"Compiled policy bundle for {agent_id}",
            },
            "shadow_mode": False,
            "rules": compiled_rules,
        }

        # 3. Retrieve Revocation List
        revocation_list = []
        if self.authority_service:
            revocation_list = self.authority_service.list_revoked_authorities(tenant_id)

        # 4. Compute SHA-256 Bundle Digest
        payload_json = json.dumps(policy_payload, sort_keys=True)
        bundle_digest = hashlib.sha256(payload_json.encode("utf-8")).hexdigest()

        # 5. Sign Bundle with KeyManager
        active_key_id, active_secret = self.key_manager.get_active_key()
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(seconds=ttl_seconds)
        bundle_id = f"bundle_{uuid.uuid4().hex[:10]}"

        signature_payload = f"{bundle_id}:{tenant_id}:{agent_id}:{environment}:{bundle_digest}:{active_key_id}:{now.isoformat()}:{expires_at.isoformat()}"
        signature = hmac.new(
            active_secret, signature_payload.encode("utf-8"), hashlib.sha256
        ).hexdigest()

        bundle = SignedPolicyBundle(
            bundle_id=bundle_id,
            tenant_id=tenant_id,
            agent_id=agent_id,
            environment=environment,
            policy_versions=policy_versions_map,
            policy_payload=policy_payload,
            revocation_list=revocation_list,
            issued_at=now,
            expires_at=expires_at,
            bundle_digest=bundle_digest,
            key_id=active_key_id,
            signature=signature,
        )

        if self.audit_service:
            self.audit_service.record_event(
                "BUNDLE_ISSUED",
                tenant_id,
                "system",
                "bundle",
                bundle_id,
                {"agent_id": agent_id},
            )

        return bundle

    def verify_bundle_signature(self, bundle: SignedPolicyBundle) -> bool:
        # 1. Expiration check
        if bundle.is_expired():
            return False

        # 2. Key lookup
        secret_bytes = self.key_manager.get_key(bundle.key_id)
        if not secret_bytes:
            return False

        # 3. Verify Bundle Payload SHA-256 Digest
        payload_json = json.dumps(bundle.policy_payload, sort_keys=True)
        expected_digest = hashlib.sha256(payload_json.encode("utf-8")).hexdigest()
        if expected_digest != bundle.bundle_digest:
            return False

        # 4. Verify HMAC Signature
        signature_payload = f"{bundle.bundle_id}:{bundle.tenant_id}:{bundle.agent_id}:{bundle.environment}:{bundle.bundle_digest}:{bundle.key_id}:{bundle.issued_at.isoformat()}:{bundle.expires_at.isoformat()}"
        expected_sig = hmac.new(
            secret_bytes, signature_payload.encode("utf-8"), hashlib.sha256
        ).hexdigest()

        return hmac.compare_digest(bundle.signature, expected_sig)
