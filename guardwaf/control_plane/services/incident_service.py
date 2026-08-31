"""
Incident Management & Audit Timeline Correlation Service.
"""

import uuid
from datetime import datetime, timezone
from typing import Optional, List, Dict
from guardwaf.control_plane.models.incident import Incident, IncidentSeverity, IncidentStatus
from guardwaf.control_plane.repositories.base import AuditRepository
from guardwaf.exceptions import GuardWAFConfigurationError, GuardWAFSecurityError

class IncidentService:
    def __init__(self, audit_repo: AuditRepository):
        self.audit_repo = audit_repo
        self._incidents: Dict[str, Incident] = {}

    def create_incident(
        self,
        organization_id: str,
        agent_id: str,
        title: str,
        description: Optional[str] = None,
        severity: IncidentSeverity = IncidentSeverity.HIGH,
        correlation_id: Optional[str] = None
    ) -> Incident:
        inc_id = f"inc_{uuid.uuid4().hex[:10]}"
        
        # Correlate audit events if correlation_id is present
        related_ids = []
        if correlation_id:
            events = self.audit_repo.list_audit_events(organization_id)
            related_ids = [e.event_id for e in events if e.metadata.get("correlation_id") == correlation_id]

        inc = Incident(
            incident_id=inc_id,
            organization_id=organization_id,
            agent_id=agent_id,
            title=title,
            description=description,
            severity=severity,
            status=IncidentStatus.OPEN,
            related_event_ids=related_ids,
            correlation_id=correlation_id
        )
        self._incidents[inc_id] = inc
        return inc

    def resolve_incident(self, organization_id: str, incident_id: str, resolved_by: str = "security_admin") -> Incident:
        inc = self._incidents.get(incident_id)
        if not inc:
            raise GuardWAFConfigurationError(f"Incident '{incident_id}' not found.")
        if inc.organization_id != organization_id:
            raise GuardWAFSecurityError("Cross-tenant incident access denied.", tool_name="incident_service")

        inc.status = IncidentStatus.RESOLVED
        inc.resolved_at = datetime.now(timezone.utc)
        inc.resolved_by = resolved_by
        return inc

    def list_incidents(self, organization_id: str) -> List[Incident]:
        return [inc for inc in self._incidents.values() if inc.organization_id == organization_id]
