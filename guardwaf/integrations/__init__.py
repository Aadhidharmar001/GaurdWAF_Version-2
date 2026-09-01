"""
GuardWAF Universal Framework Integration Adapters.
"""

from guardwaf.integrations.base import BaseFrameworkAdapter
from guardwaf.integrations.crewai import CrewAIAdapter, protect_crewai_tool
from guardwaf.integrations.custom import CustomAgentAdapter
from guardwaf.integrations.langchain import LangChainAdapter
from guardwaf.integrations.langchain import protect_tool as protect_langchain_tool
from guardwaf.integrations.langgraph import LangGraphAdapter, protect_langgraph_tool

__all__ = [
    "BaseFrameworkAdapter",
    "CrewAIAdapter",
    "CustomAgentAdapter",
    "LangChainAdapter",
    "LangGraphAdapter",
    "protect_crewai_tool",
    "protect_langchain_tool",
    "protect_langgraph_tool",
]
