"""
MCP Server Tool Execution Wrapper (Mode 1 & In-Process Integration).
Wraps MCP server tool registrations with pre-execution GuardWAF authorization.
Guarantees downstream tool bodies execute ZERO times when blocked.
"""

from typing import Any, Callable, Optional

from guardwaf.core.action_envelope import ActionEnvelope
from guardwaf.exceptions import GuardWAFSecurityError
from guardwaf.sdk.client import GuardWAF
from guardwaf.sdk.runtime_adapter import AgentRuntimeAdapter


class MCPToolWrapper:
    def __init__(
        self,
        func: Callable,
        tool_name: str,
        waf: GuardWAF,
        adapter: Optional[AgentRuntimeAdapter] = None,
    ):
        self.func = func
        self.tool_name = tool_name
        self.waf = waf
        self.adapter = adapter or AgentRuntimeAdapter(waf=waf)
        self.execution_count = 0  # Execution counter for zero-call verification!

    def __call__(self, *args, **kwargs) -> Any:
        # Canonicalize arguments
        params = kwargs.copy()
        if args and hasattr(self.func, "__code__"):
            code_args = self.func.__code__.co_varnames[: len(args)]
            for name, val in zip(code_args, args):
                params[name] = val

        envelope = ActionEnvelope(
            protocol="mcp",
            tenant_id=kwargs.get("tenant_id", "default"),
            agent_id=kwargs.get("agent_id", "mcp_agent"),
            tool_name=self.tool_name,
            parameters=params,
        )

        allowed, reason, grant, pending = self.adapter.authorize_action(envelope)
        if not allowed:
            raise GuardWAFSecurityError(
                reason or f"MCP tool '{self.tool_name}' blocked by GuardWAF policy.",
                tool_name=self.tool_name,
            )

        # Execute downstream tool
        self.execution_count += 1
        return self.func(*args, **kwargs)


def secure_server(mcp_server: Any, waf: GuardWAF) -> Any:
    """
    Wraps all registered tools on an MCP server instance with GuardWAF pre-execution governance.
    """
    if hasattr(mcp_server, "tools"):
        for name, tool_func in mcp_server.tools.items():
            mcp_server.tools[name] = MCPToolWrapper(tool_func, tool_name=name, waf=waf)
    return mcp_server
