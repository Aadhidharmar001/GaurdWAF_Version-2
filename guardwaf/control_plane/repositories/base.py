"""
Abstract Repository Interfaces for Control Plane Entities.
"""

from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any
from guardwaf.control_plane.models.agent import AgentRecord, AgentStatus
from guardwaf.control_plane.models.policy import PolicyRecord, PolicyVersion, PolicyAssignment, PolicyStatus
from guardwaf.control_plane.models.authority import CentralAuthorityRecord, AuthorityStatus
from guardwaf.control_plane.models.audit import AuditEvent

class AgentRepository(ABC):
    @abstractmethod
    def save_agent(self, agent: AgentRecord) -> None: pass
    @abstractmethod
    def get_agent(self, agent_id: str) -> Optional[AgentRecord]: pass
    @abstractmethod
    def list_agents(self, tenant_id: str) -> List[AgentRecord]: pass

class PolicyRepository(ABC):
    @abstractmethod
    def save_policy(self, policy: PolicyRecord) -> None: pass
    @abstractmethod
    def get_policy(self, policy_id: str) -> Optional[PolicyRecord]: pass
    @abstractmethod
    def list_policies(self, tenant_id: str) -> List[PolicyRecord]: pass
    @abstractmethod
    def save_policy_version(self, version: PolicyVersion) -> None: pass
    @abstractmethod
    def get_policy_version(self, policy_id: str, version_number: int) -> Optional[PolicyVersion]: pass
    @abstractmethod
    def list_policy_versions(self, policy_id: str) -> List[PolicyVersion]: pass
    @abstractmethod
    def save_assignment(self, assignment: PolicyAssignment) -> None: pass
    @abstractmethod
    def list_assignments(self, tenant_id: str, agent_id: Optional[str] = None, environment: str = "production") -> List[PolicyAssignment]: pass

class AuthorityRepository(ABC):
    @abstractmethod
    def save_authority(self, authority: CentralAuthorityRecord) -> None: pass
    @abstractmethod
    def get_authority(self, authority_id: str) -> Optional[CentralAuthorityRecord]: pass
    @abstractmethod
    def list_authorities(self, tenant_id: str, agent_id: Optional[str] = None) -> List[CentralAuthorityRecord]: pass

class AuditRepository(ABC):
    @abstractmethod
    def save_audit_event(self, event: AuditEvent) -> None: pass
    @abstractmethod
    def list_audit_events(self, tenant_id: str) -> List[AuditEvent]: pass
