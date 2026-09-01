"""
GuardWAF Model Context Protocol (MCP) Security Gateway & Proxy Module.
"""

from guardwaf.mcp.gateway import MCPGatewayProxy
from guardwaf.mcp.models import (
    MCPSecurityDecision,
    MCPToolMetadata,
    MCPToolRequest,
    MCPToolResponse,
)
from guardwaf.mcp.wrapper import secure_server

__all__ = [
    "MCPGatewayProxy",
    "MCPSecurityDecision",
    "MCPToolMetadata",
    "MCPToolRequest",
    "MCPToolResponse",
    "secure_server",
]
