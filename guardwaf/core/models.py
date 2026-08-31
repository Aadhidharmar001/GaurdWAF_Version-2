"""
Core Data Models for GuardWAF Action Authorization Engine.
"""

import enum
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from pydantic import BaseModel, Field

class ActionState(str, enum.Enum):
    CREATED = "CREATED"
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    DENIED = "DENIED"
    EXPIRED = "EXPIRED"
    EXECUTING = "EXECUTING"
    EXECUTED = "EXECUTED"

class SessionContext(BaseModel):
    session_id: str
    principal_id: Optional[str] = None
    customer_id: Optional[str] = None
    tenant_id: Optional[str] = "default"
    user_role: Optional[str] = "user"
    allowed_scope_ids: List[str] = Field(default_factory=list)

class AgentIdentity(BaseModel):
    agent_id: str
    owning_team: Optional[str] = "engineering"
    approved_scopes: List[str] = Field(default_factory=list)
    status: str = "active"

class ActionIntent(BaseModel):
    intent_id: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    agent_id: str
    tool_name: str
    parameters: Dict[str, Any] = Field(default_factory=dict)
    parameter_digest: str
    session_context: Optional[SessionContext] = None

class ActionGrant(BaseModel):
    grant_id: str
    issuer: str = "guardwaf-local-engine"
    subject_agent: str
    principal_id: Optional[str] = None
    tenant_id: Optional[str] = "default"
    delegated_authority_id: Optional[str] = None
    session_id: str

    target_action: str
    parameter_digest: str
    policy_version: str = "v1"
    key_id: str = "k1"
    issued_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: datetime
    nonce: str
    signature: str


class PendingAction(BaseModel):
    pending_action_id: str
    tenant_id: Optional[str] = "default"
    agent_id: str

    delegating_principal: Optional[str] = None
    session_id: str
    tool_name: str
    canonical_parameters: str
    parameters: Dict[str, Any] = Field(default_factory=dict)
    parameter_digest: str
    action_intent_digest: str
    policy_decision: str = "pending_hitl"
    matched_rule: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: datetime
    status: ActionState = ActionState.PENDING
    approver_id: Optional[str] = None
    approved_at: Optional[datetime] = None
    denied_reason: Optional[str] = None
    execution_status: str = "UNEXECUTED"
    idempotency_key: str
    approval_token: Optional[str] = None

class RuleResult(BaseModel):
    status: str  # "allowed", "blocked", "pending_hitl", "shadow_blocked"
    outcome: str
    matched_rule: Optional[str] = None
    risk_score: Optional[float] = 0.0
    risk_level: Optional[str] = "LOW"
    entropy: Optional[float] = 0.0
    owasp_code: Optional[str] = "LLM06"
    risk_factors: List[str] = Field(default_factory=list)
    hitl_id: Optional[str] = None
    hitl_approval_token: Optional[str] = None
    pending_action: Optional[PendingAction] = None

# --- Policy Rule Configurations ---

class RateLimitRule(BaseModel):
    tool: str
    max_calls: int = Field(alias="max_calls_per_minute", default=10)
    window_seconds: int = 60
    action: str = "block"
    shadow_mode: bool = False

    class Config:
        populate_by_name = True

class SequenceRule(BaseModel):
    tool: str
    required_predecessor: Optional[str] = None
    requires: List[str] = Field(default_factory=list)
    action: str = "block"
    shadow_mode: bool = False

    def get_predecessors(self) -> List[str]:
        if self.requires:
            return self.requires
        if self.required_predecessor:
            return [self.required_predecessor]
        return []

class BulkThresholdRule(BaseModel):
    tool: str
    param_name: str
    max_value: int
    action: str = "block"
    shadow_mode: bool = False

class DataScopeRule(BaseModel):
    tool: str
    param_name: str
    pattern: Optional[str] = None
    check_session_customer_id: bool = False
    action: str = "block"
    shadow_mode: bool = False

class ParameterBlocklistRule(BaseModel):
    tool: str
    param_name: str
    blocklist: List[str]
    action: str = "block"
    shadow_mode: bool = False

class HITLRule(BaseModel):
    tool: str
    condition_param: Optional[str] = None
    greater_than: Optional[float] = None
    action: str = "require_hitl"
    shadow_mode: bool = False

class PolicyRules(BaseModel):
    rate_limits: List[RateLimitRule] = Field(default_factory=list)
    sequences: List[SequenceRule] = Field(default_factory=list)
    bulk_thresholds: List[BulkThresholdRule] = Field(default_factory=list)
    data_scope: List[DataScopeRule] = Field(default_factory=list)
    parameter_blocklist: List[ParameterBlocklistRule] = Field(default_factory=list)
    hitl_rules: List[HITLRule] = Field(default_factory=list)

class PolicyMetadata(BaseModel):
    policy_name: str
    version: str = "1.0"
    description: Optional[str] = "GuardWAF Security Policy"

class PolicyConfig(BaseModel):
    metadata: PolicyMetadata
    shadow_mode: bool = False
    rules: PolicyRules
