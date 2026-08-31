"""
Enterprise Policy Management, Versioning, Validation, and Rollback Service.
"""

import json
import hashlib
import uuid
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from guardwaf.control_plane.models.policy import PolicyRecord, PolicyVersion, PolicyAssignment, PolicyStatus
from guardwaf.control_plane.repositories.base import PolicyRepository
from guardwaf.control_plane.services.audit_service import AuditService
from guardwaf.exceptions import GuardWAFConfigurationError, GuardWAFSecurityError

class PolicyService:
    def __init__(self, repo: PolicyRepository, audit_service: Optional[AuditService] = None):
        self.repo = repo
        self.audit_service = audit_service

    def create_policy(self, tenant_id: str, name: str, description: Optional[str] = None, actor_id: str = "admin") -> PolicyRecord:
        policy_id = f"pol_{uuid.uuid4().hex[:10]}"
        record = PolicyRecord(
            policy_id=policy_id,
            tenant_id=tenant_id,
            name=name,
            description=description,
            status=PolicyStatus.DRAFT,
            created_by=actor_id
        )
        self.repo.save_policy(record)
        if self.audit_service:
            self.audit_service.record_event("POLICY_CREATED", tenant_id, actor_id, "policy", policy_id, {"name": name})
        return record

    def create_version(self, policy_id: str, rules: Dict[str, Any], actor_id: str = "admin") -> PolicyVersion:
        policy = self.repo.get_policy(policy_id)
        if not policy:
            raise GuardWAFConfigurationError(f"Policy '{policy_id}' not found.")

        existing_versions = self.repo.list_policy_versions(policy_id)
        next_ver = max([v.version_number for v in existing_versions], default=0) + 1

        # Compute SHA-256 Digest of immutable rules content
        rules_json = json.dumps(rules, sort_keys=True)
        content_digest = hashlib.sha256(rules_json.encode('utf-8')).hexdigest()

        version = PolicyVersion(
            version_id=f"pv_{uuid.uuid4().hex[:10]}",
            policy_id=policy_id,
            version_number=next_ver,
            rules=rules,
            created_by=actor_id,
            content_digest=content_digest
        )
        self.repo.save_policy_version(version)

        if self.audit_service:
            self.audit_service.record_event("POLICY_VERSION_CREATED", policy.tenant_id, actor_id, "policy_version", version.version_id, {"version_number": next_ver})

        return version

    def publish_and_activate(self, policy_id: str, version_number: int, actor_id: str = "admin") -> PolicyRecord:
        policy = self.repo.get_policy(policy_id)
        if not policy:
            raise GuardWAFConfigurationError(f"Policy '{policy_id}' not found.")

        version = self.repo.get_policy_version(policy_id, version_number)
        if not version:
            raise GuardWAFConfigurationError(f"Policy version v{version_number} not found for policy '{policy_id}'.")

        policy.status = PolicyStatus.ACTIVE
        policy.active_version = version_number
        self.repo.save_policy(policy)

        if self.audit_service:
            self.audit_service.record_event("POLICY_ACTIVATED", policy.tenant_id, actor_id, "policy", policy_id, {"active_version": version_number})

        return policy

    def rollback_version(self, policy_id: str, target_version_number: int, actor_id: str = "admin") -> PolicyRecord:
        policy = self.repo.get_policy(policy_id)
        if not policy:
            raise GuardWAFConfigurationError(f"Policy '{policy_id}' not found.")

        target_version = self.repo.get_policy_version(policy_id, target_version_number)
        if not target_version:
            raise GuardWAFConfigurationError(f"Target version v{target_version_number} not found for rollback.")

        old_version = policy.active_version
        policy.active_version = target_version_number
        policy.status = PolicyStatus.ACTIVE
        self.repo.save_policy(policy)

        if self.audit_service:
            self.audit_service.record_event(
                "POLICY_ROLLED_BACK",
                policy.tenant_id,
                actor_id,
                "policy",
                policy_id,
                {"from_version": old_version, "to_version": target_version_number}
            )

        return policy

    def assign_policy(
        self,
        tenant_id: str,
        policy_id: str,
        agent_id: Optional[str] = None,
        environment: str = "production"
    ) -> PolicyAssignment:
        assignment = PolicyAssignment(
            assignment_id=f"passign_{uuid.uuid4().hex[:10]}",
            tenant_id=tenant_id,
            agent_id=agent_id,
            environment=environment,
            policy_id=policy_id
        )
        self.repo.save_assignment(assignment)
        return assignment
