"""
GuardWAF Universal Framework Integration Adapters.
"""

from guardwaf.integrations.base import BaseFrameworkAdapter
from guardwaf.integrations.langchain import LangChainAdapter, protect_tool as protect_langchain_tool
from guardwaf.integrations.langgraph import LangGraphAdapter, protect_langgraph_tool
from guardwaf.integrations.crewai import CrewAIAdapter, protect_crewai_tool
from guardwaf.integrations.custom import CustomAgentAdapter

__all__ = [
    "BaseFrameworkAdapter",
    "LangChainAdapter",
    "protect_langchain_tool",
    "LangGraphAdapter",
    "protect_langgraph_tool",
    "CrewAIAdapter",
    "protect_crewai_tool",
    "CustomAgentAdapter",
]
