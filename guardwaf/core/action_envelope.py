"""
Universal Transport-Neutral Action Envelope Model & Parameter Canonicalization.
Acts as the unified contract between external runtime adapters (LangChain, CrewAI, MCP, Custom) and the GuardWAF Engine.
"""

import uuid
from datetime import datetime, timezone
from typing import Any, Dict

from pydantic import BaseModel, Field


def compute_envelope_digest(parameters: Dict[str, Any]) -> str:
    """
    Computes a SHA-256 canonical digest of parameter values matching the core engine specification.
    """
    from guardwaf.core.canonical import compute_parameter_digest

    return compute_parameter_digest(parameters)


class ActionEnvelope(BaseModel):
    """
    Universal transport-neutral action envelope representing a tool call request across any agent framework or transport protocol.
    """

    envelope_id: str = Field(default_factory=lambda: f"env_{uuid.uuid4().hex[:10]}")
    protocol: str = "python"  # "python", "langchain", "crewai", "mcp", "http", "custom"
    tenant_id: str = "default"
    agent_id: str = "default_agent"
    principal_id: str = "anonymous"
    session_id: str = Field(default_factory=lambda: f"sess_{uuid.uuid4().hex[:10]}")
    tool_name: str
    parameters: Dict[str, Any] = Field(default_factory=dict)
    parameter_digest: str = ""
    correlation_id: str = Field(default_factory=lambda: f"corr_{uuid.uuid4().hex[:10]}")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = Field(default_factory=dict)

    def model_post_init(self, __context: Any) -> None:
        if not self.parameter_digest:
            self.parameter_digest = compute_envelope_digest(self.parameters)
