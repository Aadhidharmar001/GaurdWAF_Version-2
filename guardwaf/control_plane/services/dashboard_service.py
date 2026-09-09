"""
Security Operations Dashboard Service providing overview statistics and activity streams.
"""

from typing import Any, Dict, List

from guardwaf.control_plane.repositories.base import AgentRepository, AuditRepository


class DashboardService:
    def __init__(self, agent_repo: AgentRepository, audit_repo: AuditRepository):
        self.agent_repo = agent_repo
        self.audit_repo = audit_repo

    def get_overview_stats(self, tenant_id: str) -> Dict[str, Any]:
        agents = self.agent_repo.list_agents(tenant_id)
        events = self.audit_repo.list_audit_events(tenant_id)

        active_count = sum(1 for a in agents if a.status.value == "ACTIVE")
        revoked_count = sum(1 for a in agents if a.status.value == "REVOKED")

        allowed_count = sum(1 for e in events if e.metadata.get("decision") == "ALLOW" or e.event_type == "ACTION_ALLOWED")
        blocked_count = sum(1 for e in events if e.metadata.get("decision") == "BLOCK" or e.event_type == "ACTION_BLOCKED")
        hitl_count = sum(1 for e in events if e.metadata.get("decision") == "REQUIRE_HITL" or e.event_type == "HITL_REQUIRED")

        return {
            "tenant_id": tenant_id,
            "total_agents": len(agents),
            "active_agents": active_count,
            "revoked_agents": revoked_count,
            "total_audit_events": len(events),
            "allowed_actions": allowed_count,
            "blocked_actions": blocked_count,
            "pending_hitl_actions": hitl_count,
        }

    def get_live_activity_stream(self, tenant_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        events = self.audit_repo.list_audit_events(tenant_id)
        # Sort descending by timestamp
        sorted_events = sorted(events, key=lambda e: e.timestamp, reverse=True)[:limit]
        return [e.model_dump() for e in sorted_events]
