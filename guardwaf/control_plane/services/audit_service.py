"""
Audit Logging Service for Recording Control Plane Admin Operations.
"""

import uuid
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from guardwaf.control_plane.models.audit import AuditEvent
from guardwaf.control_plane.repositories.base import AuditRepository

class AuditService:
    def __init__(self, repo: AuditRepository):
        self.repo = repo

    def record_event(
        self,
        event_type: str,
        tenant_id: str,
        actor_id: str,
        resource_type: str,
        resource_id: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> AuditEvent:
        event = AuditEvent(
            event_id=f"audit_{uuid.uuid4().hex[:12]}",
            event_type=event_type,
            tenant_id=tenant_id,
            actor_id=actor_id,
            resource_type=resource_type,
            resource_id=resource_id,
            timestamp=datetime.now(timezone.utc),
            metadata=metadata or {}
        )
        self.repo.save_audit_event(event)
        return event

    def list_events(self, tenant_id: str) -> List[AuditEvent]:
        return self.repo.list_audit_events(tenant_id)
