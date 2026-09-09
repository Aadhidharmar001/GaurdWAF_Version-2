"""
CrewAI Framework Adapter for GuardWAF Pre-Execution Tool Governance.
Translates CrewAI tool invocations to ActionEnvelope and delegates 100% of policy evaluation to GuardWAF engine.
"""

from typing import Any, Callable, Optional

from guardwaf.exceptions import GuardWAFSecurityError
from guardwaf.integrations.base import BaseFrameworkAdapter
from guardwaf.sdk.client import GuardWAF


class DummyCrewAITool:
    """Mock/Fallback CrewAI tool container for testing when crewai package is not installed."""

    def __init__(self, name: str, func: Callable, description: str = ""):
        self.name = name
        self.func = func
        self.description = description
        self.execution_count = 0

    def _run(self, *args, **kwargs) -> Any:
        return self.func(*args, **kwargs)

    def run(self, *args, **kwargs) -> Any:
        return self._run(*args, **kwargs)

    def __call__(self, *args, **kwargs) -> Any:
        return self._run(*args, **kwargs)


class CrewAIAdapter(BaseFrameworkAdapter):
    def __init__(self, waf: GuardWAF):
        super().__init__(waf=waf, protocol_name="crewai")

    def wrap_tool(self, tool: Any, tool_name: Optional[str] = None) -> Any:
        t_name = tool_name or getattr(tool, "name", getattr(tool, "__name__", "crewai_tool"))
        execution_counter = {"count": 0}

        target_func = getattr(tool, "_run", tool)

        def _protected_run(*args, **kwargs):
            params = kwargs.copy()
            if args:
                params["args"] = list(args)

            allowed, reason, grant, pending = self.evaluate_envelope(
                tool_name=t_name,
                parameters=params,
                tenant_id=kwargs.get("tenant_id", "default"),
                agent_id=kwargs.get("agent_id", "crewai_agent"),
            )

            if not allowed:
                raise GuardWAFSecurityError(
                    reason or f"CrewAI tool '{t_name}' blocked by GuardWAF policy.",
                    tool_name=t_name,
                )

            execution_counter["count"] += 1
            if callable(target_func):
                return target_func(*args, **kwargs)
            return target_func

        _protected_run.execution_counter = execution_counter

        if hasattr(tool, "_run"):
            tool._run = _protected_run
            return tool

        return DummyCrewAITool(
            name=t_name,
            func=_protected_run,
            description=getattr(tool, "description", ""),
        )


def protect_tool(tool: Any, waf: GuardWAF, tool_name: Optional[str] = None) -> Any:
    adapter = CrewAIAdapter(waf=waf)
    return adapter.wrap_tool(tool, tool_name=tool_name)


protect_crewai_tool = protect_tool
