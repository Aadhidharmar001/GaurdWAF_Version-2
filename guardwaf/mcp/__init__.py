"""
GuardWAF Model Context Protocol (MCP) Security Gateway & Proxy Module.
"""

from guardwaf.mcp.gateway import MCPGatewayProxy
from guardwaf.mcp.models import MCPToolRequest, MCPToolResponse, MCPSecurityDecision, MCPToolMetadata
from guardwaf.mcp.wrapper import secure_server

__all__ = [
    "MCPGatewayProxy",
    "MCPToolRequest",
    "MCPToolResponse",
    "MCPSecurityDecision",
    "MCPToolMetadata",
    "secure_server",
]
