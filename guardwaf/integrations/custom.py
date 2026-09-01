"""
Custom Agent Runtime Adapter.
Allows any custom Python agent or tool runtime to easily integrate with GuardWAF.
"""

from typing import Callable, Optional

from guardwaf.exceptions import GuardWAFSecurityError
from guardwaf.integrations.base import BaseFrameworkAdapter
from guardwaf.sdk.client import GuardWAF


class CustomAgentAdapter(BaseFrameworkAdapter):
    def __init__(self, waf: GuardWAF):
        super().__init__(waf=waf, protocol_name="custom")

    def wrap_tool(self, func: Callable, tool_name: Optional[str] = None) -> Callable:
        t_name = tool_name or getattr(func, "__name__", "custom_tool")
        execution_counter = {"count": 0}

        def _wrapped(*args, **kwargs):
            params = kwargs.copy()
            if args and hasattr(func, "__code__"):
                code_args = func.__code__.co_varnames[: len(args)]
                for name, val in zip(code_args, args):
                    params[name] = val

            allowed, reason, grant, pending = self.evaluate_envelope(
                tool_name=t_name,
                parameters=params,
                tenant_id=kwargs.get("tenant_id", "default"),
                agent_id=kwargs.get("agent_id", "custom_agent"),
            )

            if not allowed:
                raise GuardWAFSecurityError(
                    reason or f"Custom tool '{t_name}' blocked by GuardWAF policy.",
                    tool_name=t_name,
                )

            execution_counter["count"] += 1
            return func(*args, **kwargs)

        _wrapped.execution_counter = execution_counter
        return _wrapped
