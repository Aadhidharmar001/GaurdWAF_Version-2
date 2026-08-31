from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

# --- Session Context & Request Schemas ---

class SessionContext(BaseModel):
    customer_id: Optional[str] = None
    user_role: Optional[str] = "user"
    allowed_scope_ids: List[str] = []

class AgentIdentity(BaseModel):
    agent_id: str
    owning_team: Optional[str] = "engineering"
    approved_scopes: List[str] = []
    status: str = "active"

class ToolCallRequest(BaseModel):
    agent_id: str
    session_id: str
    tool: str
    parameters: Dict[str, Any] = Field(default_factory=dict)
    session_context: Optional[SessionContext] = None

class RuleResult(BaseModel):
    status: str  # "allowed", "blocked", "pending_hitl", "shadow_blocked"
    outcome: str
    matched_rule: Optional[str] = None
    risk_score: Optional[float] = 0.0
    risk_level: Optional[str] = "LOW"
    entropy: Optional[float] = 0.0
    owasp_code: Optional[str] = "LLM06"
    risk_factors: List[str] = Field(default_factory=list)

class ToolCallResponse(BaseModel):
    status: str
    message: str
    evaluation_details: Dict[str, Any]
    result: Optional[Any] = None

class HITLDecision(BaseModel):
    decision: str  # "approve" or "reject"
    reason: Optional[str] = None


# --- Policy & Rule Definition Schemas ---

class RateLimitRule(BaseModel):
    tool: str
    max_calls_per_minute: int
    action: str = "block"
    shadow_mode: bool = False

class SequenceRule(BaseModel):
    tool: str
    required_predecessor: str
    action: str = "block"
    shadow_mode: bool = False

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
    action: str = "require_hitl"
    shadow_mode: bool = False

class ParameterBlocklistRule(BaseModel):
    tool: str
    param_name: str
    blocklist: List[str]
    action: str = "block"
    shadow_mode: bool = False

class PolicyRules(BaseModel):
    rate_limits: List[RateLimitRule] = []
    sequences: List[SequenceRule] = []
    bulk_thresholds: List[BulkThresholdRule] = []
    data_scope: List[DataScopeRule] = []
    parameter_blocklist: List[ParameterBlocklistRule] = []

class PolicyMetadata(BaseModel):
    policy_name: str
    version: str
    description: str

class PolicyConfig(BaseModel):
    metadata: PolicyMetadata
    shadow_mode: bool = False
    rules: PolicyRules
