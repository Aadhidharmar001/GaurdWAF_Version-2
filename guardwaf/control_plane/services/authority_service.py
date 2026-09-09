"""
Central Delegated Authority Lifecycle & Revocation Management Service.
"""

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from guardwaf.control_plane.models.authority import (
    AuthorityStatus,
    CentralAuthorityRecord,
)
from guardwaf.control_plane.repositories.base import AuthorityRepository
from guardwaf.control_plane.services.audit_service import AuditService
from guardwaf.exceptions import GuardWAFConfigurationError


class AuthorityService:
    def __init__(self, repo: AuthorityRepository, audit_service: Optional[AuditService] = None):
        self.repo = repo
        self.audit_service = audit_service

    def issue_authority(
        self,
        tenant_id: str,
        principal_id: str,
        agent_id: str,
        allowed_actions: List[str],
        constraints: Optional[Dict[str, Dict[str, Any]]] = None,
        expires_at: Optional[datetime] = None,
        actor_id: str = "admin",
    ) -> CentralAuthorityRecord:
        authority_id = f"auth_c_{uuid.uuid4().hex[:10]}"
        record = CentralAuthorityRecord(
            authority_id=authority_id,
            tenant_id=tenant_id,
            principal_id=principal_id,
            agent_id=agent_id,
            allowed_actions=allowed_actions,
            constraints=constraints or {},
            status=AuthorityStatus.ACTIVE,
            expires_at=expires_at or (datetime.now(timezone.utc) + datetime.timedelta(hours=24)),
        )
        self.repo.save_authority(record)
        if self.audit_service:
            self.audit_service.record_event("AUTHORITY_ISSUED", tenant_id, actor_id, "authority", authority_id)
        return record

    def revoke_authority(
        self,
        authority_id: str,
        actor_id: str = "admin",
        reason: str = "Revoked by admin",
    ) -> CentralAuthorityRecord:
        record = self.repo.get_authority(authority_id)
        if not record:
            raise GuardWAFConfigurationError(f"Authority '{authority_id}' not found.")

        now = datetime.now(timezone.utc)
        record.status = AuthorityStatus.REVOKED
        record.revoked_at = now
        record.revoked_by = actor_id
        record.revocation_reason = reason
        self.repo.save_authority(record)

        if self.audit_service:
            self.audit_service.record_event(
                "AUTHORITY_REVOKED",
                record.tenant_id,
                actor_id,
                "authority",
                authority_id,
                {"reason": reason},
            )

        return record

    def list_revoked_authorities(self, tenant_id: str) -> List[str]:
        authorities = self.repo.list_authorities(tenant_id)
        return [a.authority_id for a in authorities if a.status == AuthorityStatus.REVOKED]
