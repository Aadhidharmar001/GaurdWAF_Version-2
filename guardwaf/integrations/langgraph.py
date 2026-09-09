"""
LangGraph Framework Adapter for GuardWAF Pre-Execution State Tool Governance.
Translates LangGraph node/tool calls into ActionEnvelope and evaluates GuardWAF security policies.
"""

from typing import Callable, Optional

from guardwaf.exceptions import GuardWAFSecurityError
from guardwaf.integrations.base import BaseFrameworkAdapter
from guardwaf.sdk.client import GuardWAF


class LangGraphAdapter(BaseFrameworkAdapter):
    """
    Adapter for securing LangGraph state node tool execution.
    """

    def __init__(self, waf: GuardWAF):
        super().__init__(waf=waf, protocol_name="langgraph")

    def wrap_tool(self, tool_func: Callable, tool_name: Optional[str] = None) -> Callable:
        t_name = tool_name or getattr(tool_func, "__name__", "langgraph_tool")

        def _protected_node_execution(*args, **kwargs):
            params = {}
            if args:
                if isinstance(args[0], dict):
                    params.update(args[0])
                else:
                    params["input"] = args[0]
            params.update(kwargs)

            from guardwaf.sdk.context import get_current_execution_context

            exec_ctx = get_current_execution_context()
            ctx_tenant = exec_ctx.tenant_id if exec_ctx and exec_ctx.tenant_id else "default"
            ctx_agent = exec_ctx.agent.agent_id if exec_ctx and exec_ctx.agent else "langgraph_agent"
            ctx_session = exec_ctx.session_id if exec_ctx and exec_ctx.session_id else "sess_default"

            allowed, reason, grant, pending = self.evaluate_envelope(
                tool_name=t_name,
                parameters=params,
                tenant_id=kwargs.get("tenant_id") or ctx_tenant,
                agent_id=kwargs.get("agent_id") or ctx_agent,
                session_id=kwargs.get("session_id") or ctx_session,
            )

            if not allowed:
                if pending:
                    from guardwaf.exceptions import GuardWAFHITLRequiredError

                    raise GuardWAFHITLRequiredError(
                        message=reason or f"Action '{t_name}' requires Human-in-the-Loop approval.",
                        pending_action_id=pending.pending_action_id,
                        tool_name=t_name,
                        hitl_id=pending.pending_action_id,
                    )
                raise GuardWAFSecurityError(
                    reason or f"LangGraph tool '{t_name}' blocked by GuardWAF policy.",
                    tool_name=t_name,
                )

            return tool_func(*args, **kwargs)

        return _protected_node_execution

    wrap_node_tool = wrap_tool


def protect_langgraph_tool(tool_func: Callable, waf: GuardWAF, tool_name: Optional[str] = None) -> Callable:
    adapter = LangGraphAdapter(waf=waf)
    return adapter.wrap_tool(tool_func, tool_name=tool_name)
