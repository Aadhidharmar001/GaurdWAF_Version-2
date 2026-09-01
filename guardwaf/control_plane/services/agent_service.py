"""
Agent Registry & Revocation Lifecycle Management Service.
"""

from datetime import datetime, timezone
from typing import List, Optional

from guardwaf.control_plane.models.agent import AgentRecord, AgentStatus
from guardwaf.control_plane.repositories.base import AgentRepository
from guardwaf.control_plane.services.audit_service import AuditService
from guardwaf.exceptions import GuardWAFConfigurationError


class AgentService:
    def __init__(
        self, repo: AgentRepository, audit_service: Optional[AuditService] = None
    ):
        self.repo = repo
        self.audit_service = audit_service

    def register_agent(
        self,
        agent_id: str,
        tenant_id: str,
        name: str,
        description: Optional[str] = None,
        version: str = "1.0.0",
        environment: str = "production",
        actor_id: str = "admin",
    ) -> AgentRecord:
        record = AgentRecord(
            agent_id=agent_id,
            tenant_id=tenant_id,
            name=name,
            description=description,
            version=version,
            environment=environment,
            status=AgentStatus.ACTIVE,
        )
        self.repo.save_agent(record)
        if self.audit_service:
            self.audit_service.record_event(
                "AGENT_CREATED",
                tenant_id,
                actor_id,
                "agent",
                agent_id,
                {"version": version},
            )
        return record

    def get_agent(self, agent_id: str) -> Optional[AgentRecord]:
        return self.repo.get_agent(agent_id)

    def list_agents(self, tenant_id: str) -> List[AgentRecord]:
        return self.repo.list_agents(tenant_id)

    def revoke_agent(
        self, agent_id: str, actor_id: str = "admin", reason: Optional[str] = None
    ) -> AgentRecord:
        agent = self.repo.get_agent(agent_id)
        if not agent:
            raise GuardWAFConfigurationError(f"Agent '{agent_id}' not found.")

        now = datetime.now(timezone.utc)
        agent.status = AgentStatus.REVOKED
        agent.revoked_at = now
        agent.revoked_by = actor_id
        agent.updated_at = now
        self.repo.save_agent(agent)

        if self.audit_service:
            self.audit_service.record_event(
                "AGENT_REVOKED",
                agent.tenant_id,
                actor_id,
                "agent",
                agent_id,
                {"reason": reason},
            )

        return agent

    def activate_agent(self, agent_id: str, actor_id: str = "admin") -> AgentRecord:
        agent = self.repo.get_agent(agent_id)
        if not agent:
            raise GuardWAFConfigurationError(f"Agent '{agent_id}' not found.")

        agent.status = AgentStatus.ACTIVE
        agent.updated_at = datetime.now(timezone.utc)
        self.repo.save_agent(agent)

        if self.audit_service:
            self.audit_service.record_event(
                "AGENT_ACTIVATED", agent.tenant_id, actor_id, "agent", agent_id
            )

        return agent
