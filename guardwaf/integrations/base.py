"""
Abstract Base Framework Adapter Interface.
Enforces thin framework translation layers without duplicating security or policy engine logic.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict

from guardwaf.core.action_envelope import ActionEnvelope
from guardwaf.sdk.client import GuardWAF
from guardwaf.sdk.runtime_adapter import AgentRuntimeAdapter


class BaseFrameworkAdapter(ABC):
    """
    Abstract Base Class for all AI Agent Framework Adapters.
    Adapters ONLY translate framework-specific tool invocations into an ActionEnvelope.
    Zero security or policy logic is implemented inside adapters!
    """

    def __init__(self, waf: GuardWAF, protocol_name: str = "custom"):
        self.waf = waf
        self.protocol_name = protocol_name
        self.runtime_adapter = AgentRuntimeAdapter(waf=waf)

    @abstractmethod
    def wrap_tool(self, tool: Any) -> Any:
        pass

    def evaluate_envelope(
        self,
        tool_name: str,
        parameters: Dict[str, Any],
        tenant_id: str = "default",
        agent_id: str = "default_agent",
        principal_id: str = "anonymous",
        session_id: str = "sess_default",
    ):
        envelope = ActionEnvelope(
            protocol=self.protocol_name,
            tenant_id=tenant_id,
            agent_id=agent_id,
            principal_id=principal_id,
            session_id=session_id,
            tool_name=tool_name,
            parameters=parameters,
        )
        return self.runtime_adapter.authorize_action(envelope)
