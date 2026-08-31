"""
DelegatedAuthority Model & Constraint Validation Module.
Represents limited, temporary authority delegated from a VerifiedPrincipal to an autonomous AgentIdentity.
"""

from datetime import datetime, timezone
from typing import Optional, List, Dict, Any, Tuple
from pydantic import BaseModel, Field, ConfigDict

class DelegatedAuthority(BaseModel):
    """
    Immutable representation of authority delegated by a VerifiedPrincipal to an AgentIdentity.
    Enforces action scopes, parameter limits, tenant boundaries, and expiration.
    """
    model_config = ConfigDict(frozen=True)

    authority_id: str
    principal_id: str
    agent_id: str
    tenant_id: str = "default"
    allowed_actions: List[str] = Field(default_factory=list)
    constraints: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    issued_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: datetime

    def is_expired(self) -> bool:
        return datetime.now(timezone.utc) > self.expires_at

    def allows_tool(self, tool_name: str) -> bool:
        if "*" in self.allowed_actions:
            return True
        return tool_name in self.allowed_actions

    def validate_constraints(self, tool_name: str, parameters: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """
        Validates tool parameters against delegated constraints (e.g. max_amount, allowed_domains).
        Returns (is_valid, failure_reason).
        """
        tool_constraints = self.constraints.get(tool_name, {})
        if not tool_constraints:
            return True, None

        # 1. Parameter Amount / Threshold Constraints
        if "max_amount" in tool_constraints and "amount" in parameters:
            max_amt = float(tool_constraints["max_amount"])
            actual_amt = float(parameters["amount"])
            if actual_amt > max_amt:
                return False, f"Requested amount ${actual_amt:.2f} exceeds delegated authority limit of ${max_amt:.2f}"

        if "max_value" in tool_constraints and "value" in parameters:
            max_val = float(tool_constraints["max_value"])
            actual_val = float(parameters["value"])
            if actual_val > max_val:
                return False, f"Parameter 'value' ({actual_val}) exceeds delegated limit of {max_val}"

        # 2. Blocklisted / Allowed Target Constraints
        if "allowed_targets" in tool_constraints:
            allowed_targets = tool_constraints["allowed_targets"]
            target = parameters.get("target") or parameters.get("recipient") or parameters.get("customer_id")
            if target and target not in allowed_targets:
                return False, f"Target '{target}' is not in delegated allowed_targets list."

        return True, None
