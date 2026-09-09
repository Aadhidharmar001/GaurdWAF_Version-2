"""
Authority Engine & Evaluation Coordinator.
Evaluates VerifiedPrincipal, AgentIdentity, Tenant Boundaries, and DelegatedAuthority BEFORE tool execution.
"""

from typing import Any, Dict, Optional, Tuple

from guardwaf.exceptions import (
    GuardWAFAuthenticationError,
    GuardWAFAuthorityExpiredError,
    GuardWAFAuthorizationError,
    GuardWAFTenantBoundaryError,
    GuardWAFUnverifiedContextError,
)
from guardwaf.sdk.context import ExecutionContext


class AuthorityEvaluator:
    """
    Evaluates trusted identity and delegated authority boundaries before tool execution.
    Fails closed if identity context is unverified in strict mode or if delegated boundaries are violated.
    """

    def __init__(self, strict_mode: bool = False):
        self.strict_mode = strict_mode

    def evaluate_authority(
        self,
        context: Optional[ExecutionContext],
        tool_name: str,
        parameters: Dict[str, Any],
    ) -> Tuple[bool, Optional[str]]:
        # 1. Execution Context Exists?
        if not context or not context.principal:
            if self.strict_mode:
                raise GuardWAFUnverifiedContextError(
                    f"Action '{tool_name}' blocked: GuardWAF strict_identity mode requires a cryptographically verified principal context."
                )
            # In legacy / dev mode, allow execution to proceed to standard policy engine
            return True, None

        principal = context.principal
        agent = context.agent
        authority = context.authority

        # 2. Verified Principal Valid & Unexpired?
        if principal.is_expired():
            raise GuardWAFAuthenticationError(
                f"Action '{tool_name}' blocked: VerifiedPrincipal '{principal.principal_id}' token has expired."
            )

        # 3. Tenant Boundary Verification (Prevent LLM parameter tenant spoofing)
        # Check if parameters contain a spoofed tenant_id
        if "tenant_id" in parameters:
            param_tenant = str(parameters["tenant_id"])
            if param_tenant != context.tenant_id:
                raise GuardWAFTenantBoundaryError(
                    f"Action '{tool_name}' blocked: Parameter tenant_id '{param_tenant}' violates verified tenant boundary '{context.tenant_id}'.",
                    tool_name=tool_name,
                )

        # 4. Delegated Authority Verification (if present)
        if authority:
            # Check Expiration
            if authority.is_expired():
                raise GuardWAFAuthorityExpiredError(
                    f"Action '{tool_name}' blocked: DelegatedAuthority token '{authority.authority_id}' has expired.",
                    tool_name=tool_name,
                )

            # Check Principal Binding
            if authority.principal_id != principal.principal_id:
                raise GuardWAFAuthorizationError(
                    f"Action '{tool_name}' blocked: DelegatedAuthority '{authority.authority_id}' belongs to principal '{authority.principal_id}', not caller '{principal.principal_id}'.",
                    tool_name=tool_name,
                    code="AUTHORITY_PRINCIPAL_MISMATCH",
                )

            # Check Agent Binding
            if agent and authority.agent_id != agent.agent_id:
                raise GuardWAFAuthorizationError(
                    f"Action '{tool_name}' blocked: DelegatedAuthority '{authority.authority_id}' was issued for agent '{authority.agent_id}', not executing agent '{agent.agent_id}'.",
                    tool_name=tool_name,
                    code="AUTHORITY_AGENT_MISMATCH",
                )

            # Check Tenant Binding
            if authority.tenant_id != context.tenant_id:
                raise GuardWAFTenantBoundaryError(
                    f"Action '{tool_name}' blocked: DelegatedAuthority tenant '{authority.tenant_id}' does not match context tenant '{context.tenant_id}'.",
                    tool_name=tool_name,
                )

            # Check Tool Authorization Scope
            if not authority.allows_tool(tool_name):
                raise GuardWAFAuthorizationError(
                    f"Action '{tool_name}' blocked: Tool is not included in DelegatedAuthority allowed_actions {authority.allowed_actions}.",
                    tool_name=tool_name,
                    code="TOOL_SCOPE_EXCEEDED",
                )

            # Check Parameter Constraints
            valid_params, constraint_reason = authority.validate_constraints(tool_name, parameters)
            if not valid_params:
                raise GuardWAFAuthorizationError(
                    f"Action '{tool_name}' blocked by DelegatedAuthority constraint: {constraint_reason}",
                    tool_name=tool_name,
                    code="DELEGATED_CONSTRAINT_VIOLATION",
                )

        return True, None
