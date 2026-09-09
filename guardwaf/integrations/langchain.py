"""
LangChain Framework Adapter for GuardWAF Pre-Execution Tool Governance.
Translates LangChain tool invocations to ActionEnvelope and delegates 100% of policy evaluation to GuardWAF engine.
"""

from typing import Any, Callable, Optional

from guardwaf.exceptions import GuardWAFSecurityError
from guardwaf.integrations.base import BaseFrameworkAdapter
from guardwaf.sdk.client import GuardWAF


class DummyLangChainTool:
    """Mock/Fallback LangChain tool container for testing when langchain package is not installed."""

    def __init__(self, name: str, func: Callable, description: str = ""):
        self.name = name
        self.func = func
        self.description = description
        self.execution_count = 0

    def run(self, tool_input: Any = None, **kwargs) -> Any:
        if tool_input is not None and not kwargs:
            return self.func(tool_input)
        return self.func(**kwargs)

    def __call__(self, *args, **kwargs) -> Any:
        if args and not kwargs:
            return self.run(args[0])
        return self.run(**kwargs)


class LangChainAdapter(BaseFrameworkAdapter):
    def __init__(self, waf: GuardWAF):
        super().__init__(waf=waf, protocol_name="langchain")

    def wrap_tool(self, tool: Any, tool_name: Optional[str] = None) -> Any:

        t_name = tool_name or getattr(tool, "name", getattr(tool, "__name__", "langchain_tool"))

        # Extract target function body
        if hasattr(tool, "_run"):
            target_func = tool._run
        elif hasattr(tool, "run"):
            target_func = tool.run
        elif callable(tool):
            target_func = tool
        else:
            raise ValueError(f"Unsupported LangChain tool type: {type(tool)}")

        execution_counter = {"count": 0}

        def _protected_run(*args, **kwargs):
            # Parse parameters
            params = {}
            if args:
                params["input"] = args[0]
            params.update(kwargs)

            ctx_tenant = "default"
            ctx_agent = "langchain_agent"
            ctx_session = "sess_default"
            from guardwaf.sdk.context import get_current_execution_context

            exec_ctx = get_current_execution_context()
            if exec_ctx and exec_ctx.tenant_id:
                ctx_tenant = exec_ctx.tenant_id
            if exec_ctx and exec_ctx.agent and exec_ctx.agent.agent_id:
                ctx_agent = exec_ctx.agent.agent_id
            if exec_ctx and exec_ctx.session_id:
                ctx_session = exec_ctx.session_id

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
                    reason or f"LangChain tool '{t_name}' blocked by GuardWAF policy.",
                    tool_name=t_name,
                )

            execution_counter["count"] += 1
            if hasattr(tool, "run") and callable(tool.run):
                return target_func(*args, **kwargs)
            return target_func(*args, **kwargs)

        # Attach wrapper counter
        _protected_run.execution_counter = execution_counter

        if hasattr(tool, "run"):
            tool.run = _protected_run
            return tool

        return DummyLangChainTool(
            name=t_name,
            func=_protected_run,
            description=getattr(tool, "description", ""),
        )


def protect_tool(tool: Any, waf: GuardWAF, tool_name: Optional[str] = None) -> Any:
    adapter = LangChainAdapter(waf=waf)
    return adapter.wrap_tool(tool, tool_name=tool_name)
