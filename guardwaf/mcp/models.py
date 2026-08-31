"""
Model Context Protocol (MCP) Security Gateway Data Models.
"""

from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field

class MCPToolMetadata(BaseModel):
    name: str
    description: Optional[str] = None
    input_schema: Dict[str, Any] = Field(default_factory=dict)

class MCPToolRequest(BaseModel):
    jsonrpc: str = "2.0"
    method: str = "tools/call"
    id: Optional[str] = "1"
    tenant_id: str = "default"
    agent_id: str = "default_agent"
    tool_name: str
    arguments: Dict[str, Any] = Field(default_factory=dict)

class MCPSecurityDecision(BaseModel):
    allowed: bool
    reason: Optional[str] = None
    grant_id: Optional[str] = None
    pending_action_id: Optional[str] = None

class MCPToolResponse(BaseModel):
    jsonrpc: str = "2.0"
    id: Optional[str] = "1"
    result: Optional[Dict[str, Any]] = None
    error: Optional[Dict[str, Any]] = None
