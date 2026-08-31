"""
Thread-safe In-Memory Control Plane Repository Implementations.
"""

import threading
from typing import Optional, List, Dict, Any
from guardwaf.control_plane.models.agent import AgentRecord
from guardwaf.control_plane.models.policy import PolicyRecord, PolicyVersion, PolicyAssignment
from guardwaf.control_plane.models.authority import CentralAuthorityRecord
from guardwaf.control_plane.models.audit import AuditEvent
from guardwaf.control_plane.repositories.base import (
    AgentRepository,
    PolicyRepository,
    AuthorityRepository,
    AuditRepository
)

class MemoryControlPlaneRepository(AgentRepository, PolicyRepository, AuthorityRepository, AuditRepository):
    def __init__(self):
        self._lock = threading.Lock()
        self._agents: Dict[str, AgentRecord] = {}
        self._policies: Dict[str, PolicyRecord] = {}
        self._policy_versions: Dict[str, Dict[int, PolicyVersion]] = {}
        self._assignments: List[PolicyAssignment] = []
        self._authorities: Dict[str, CentralAuthorityRecord] = {}
        self._audit_events: List[AuditEvent] = []

    # --- Agent Repo ---
    def save_agent(self, agent: AgentRecord) -> None:
        with self._lock:
            self._agents[agent.agent_id] = agent

    def get_agent(self, agent_id: str) -> Optional[AgentRecord]:
        with self._lock:
            return self._agents.get(agent_id)

    def list_agents(self, tenant_id: str) -> List[AgentRecord]:
        with self._lock:
            return [a for a in self._agents.values() if a.tenant_id == tenant_id]

    # --- Policy Repo ---
    def save_policy(self, policy: PolicyRecord) -> None:
        with self._lock:
            self._policies[policy.policy_id] = policy

    def get_policy(self, policy_id: str) -> Optional[PolicyRecord]:
        with self._lock:
            return self._policies.get(policy_id)

    def list_policies(self, tenant_id: str) -> List[PolicyRecord]:
        with self._lock:
            return [p for p in self._policies.values() if p.tenant_id == tenant_id]

    def save_policy_version(self, version: PolicyVersion) -> None:
        with self._lock:
            if version.policy_id not in self._policy_versions:
                self._policy_versions[version.policy_id] = {}
            self._policy_versions[version.policy_id][version.version_number] = version

    def get_policy_version(self, policy_id: str, version_number: int) -> Optional[PolicyVersion]:
        with self._lock:
            versions = self._policy_versions.get(policy_id, {})
            return versions.get(version_number)

    def list_policy_versions(self, policy_id: str) -> List[PolicyVersion]:
        with self._lock:
            versions = self._policy_versions.get(policy_id, {})
            return list(versions.values())

    def save_assignment(self, assignment: PolicyAssignment) -> None:
        with self._lock:
            self._assignments.append(assignment)

    def list_assignments(self, tenant_id: str, agent_id: Optional[str] = None, environment: str = "production") -> List[PolicyAssignment]:
        with self._lock:
            matches = []
            for a in self._assignments:
                if a.tenant_id == tenant_id and a.environment == environment:
                    if agent_id is None or a.agent_id == agent_id or a.agent_id is None:
                        matches.append(a)
            return matches

    # --- Authority Repo ---
    def save_authority(self, authority: CentralAuthorityRecord) -> None:
        with self._lock:
            self._authorities[authority.authority_id] = authority

    def get_authority(self, authority_id: str) -> Optional[CentralAuthorityRecord]:
        with self._lock:
            return self._authorities.get(authority_id)

    def list_authorities(self, tenant_id: str, agent_id: Optional[str] = None) -> List[CentralAuthorityRecord]:
        with self._lock:
            matches = []
            for auth in self._authorities.values():
                if auth.tenant_id == tenant_id:
                    if agent_id is None or auth.agent_id == agent_id:
                        matches.append(auth)
            return matches

    # --- Audit Repo ---
    def save_audit_event(self, event: AuditEvent) -> None:
        with self._lock:
            self._audit_events.append(event)

    def list_audit_events(self, tenant_id: str) -> List[AuditEvent]:
        with self._lock:
            return [e for e in self._audit_events if e.tenant_id == tenant_id]
