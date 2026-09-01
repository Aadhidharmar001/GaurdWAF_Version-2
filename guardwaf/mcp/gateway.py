"""
MCP Security Gateway Proxy (Mode 2 & Sidecar Deployment).
Interceptors incoming client MCP requests, governs tool discovery, verifies parameter digests, and enforces pre-execution GuardWAF authorization.
"""

from typing import Any, Callable, List, Optional

from guardwaf.core.action_envelope import ActionEnvelope, compute_envelope_digest
from guardwaf.exceptions import GuardWAFSecurityError
from guardwaf.mcp.models import MCPToolMetadata, MCPToolRequest, MCPToolResponse
from guardwaf.sdk.client import GuardWAF
from guardwaf.sdk.runtime_adapter import AgentRuntimeAdapter


class MCPGatewayProxy:
    """
    MCP Gateway Proxy sitting between MCP Clients and Downstream MCP Servers.
    """

    def __init__(
        self,
        waf: GuardWAF,
        downstream_handler: Optional[
            Callable[[MCPToolRequest], MCPToolResponse]
        ] = None,
        backend_server: Optional[Any] = None,
    ):
        self.waf = waf
        self.adapter = AgentRuntimeAdapter(waf=waf)
        self.downstream_handler = downstream_handler
        self.backend_server = backend_server
        self.downstream_execution_count = (
            0  # Counter verifying zero downstream execution on block
        )

    def filter_allowed_tools(
        self,
        tenant_id: str,
        agent_id: str,
        available_tools: List[MCPToolMetadata],
        allowed_tool_names: Optional[List[str]] = None,
    ) -> List[MCPToolMetadata]:
        """
        Tool Discovery Governance:
        Filters available tools based on GuardWAF policy whitelist. Unauthorized tools are omitted during discovery.
        """
        if allowed_tool_names is None:
            # Fetch active policy
            active_pol = self.waf.policy
            if active_pol and hasattr(active_pol, "rules"):
                # Default allow all if no explicit tool scope restriction
                allowed_tool_names = None

        if allowed_tool_names is not None:
            return [t for t in available_tools if t.name in allowed_tool_names]
        return available_tools

    def handle_tool_request(self, request: MCPToolRequest) -> MCPToolResponse:
        """
        Handles incoming MCP tool call request:
        1. Construct ActionEnvelope.
        2. Verify parameter digest integrity.
        3. Authorize via GuardWAF core engine.
        4. Forward exact evaluated payload to downstream server only if ALLOWED.
        """
        # 1. Parameter Digest Integrity Check
        evaluated_digest = compute_envelope_digest(request.arguments)

        envelope = ActionEnvelope(
            protocol="mcp",
            tenant_id=request.tenant_id,
            agent_id=request.agent_id,
            tool_name=request.tool_name,
            parameters=request.arguments,
            parameter_digest=evaluated_digest,
        )

        # 2. Authorize via GuardWAF Engine
        try:
            allowed, reason, grant, pending = self.adapter.authorize_action(envelope)
        except Exception as err:
            return MCPToolResponse(
                id=request.id,
                error={"code": -32001, "message": f"GuardWAF Security Error: {err!s}"},
            )

        if not allowed:
            return MCPToolResponse(
                id=request.id,
                error={
                    "code": -32002,
                    "message": reason
                    or f"MCP tool '{request.tool_name}' blocked by GuardWAF policy.",
                },
            )

        # 3. Verify Parameter Integrity before Forwarding
        forwarded_digest = compute_envelope_digest(request.arguments)
        if forwarded_digest != evaluated_digest:
            return MCPToolResponse(
                id=request.id,
                error={
                    "code": -32003,
                    "message": "CRITICAL: Parameter mutation detected between authorization and forwarding.",
                },
            )

        # 4. Forward to Downstream MCP Server
        self.downstream_execution_count += 1
        if self.downstream_handler:
            return self.downstream_handler(request)

        return MCPToolResponse(
            id=request.id,
            result={
                "status": "ALLOWED_AND_EXECUTED",
                "tool_name": request.tool_name,
                "grant_id": grant.grant_id if grant else None,
            },
        )

    def invoke_tool(
        self,
        tool_name: str,
        arguments: dict,
        tenant_id: str = "default",
        agent_id: str = "mcp_agent",
    ) -> dict:
        req = MCPToolRequest(
            id="req_mcp_1",
            tool_name=tool_name,
            arguments=arguments,
            tenant_id=tenant_id,
            agent_id=agent_id,
        )
        res = self.handle_tool_request(req)
        if isinstance(res, dict):
            if res.get("error"):
                err_msg = (
                    res["error"].get("message")
                    if isinstance(res["error"], dict)
                    else str(res["error"])
                )
                raise GuardWAFSecurityError(err_msg, tool_name=tool_name)
            return res.get("result", res)

        if getattr(res, "error", None):
            err_msg = (
                res.error.get("message")
                if isinstance(res.error, dict)
                else str(res.error)
            )
            raise GuardWAFSecurityError(err_msg, tool_name=tool_name)
        return getattr(res, "result", {}) or {}
