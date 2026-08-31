"""
GuardWAF Model Context Protocol (MCP) Server Integration Example.
Demonstrates securing MCP Gateway Server tools via MCPGatewayProxy.
"""

import sys
import os

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from guardwaf import GuardWAF, GuardWAFSecurityError
from guardwaf.core.models import PolicyConfig, PolicyRules, BulkThresholdRule
from guardwaf.mcp import MCPGatewayProxy

class MockMCPServer:
    def __init__(self):
        self.tools = {
            "fetch_file": lambda path: {"content": f"File content of {path}"},
            "delete_file": lambda path: {"deleted": path}
        }

    def call_tool(self, tool_name: str, arguments: dict):
        return self.tools[tool_name](**arguments)

def main():
    print("=================================================================")
    print("🛡️  GUARdWAF MCP GATEWAY SERVER INTEGRATION DEMO")
    print("=================================================================")

    rules = PolicyRules(bulk_thresholds=[BulkThresholdRule(tool="fetch_file", param_name="max_kb", max_value=1024)])
    policy = PolicyConfig(metadata={"policy_name": "mcp_policy"}, rules=rules)
    waf = GuardWAF(policy=policy, secret_key="mcp_demo_secret_key_32bytes_long_m")

    backend_server = MockMCPServer()
    mcp_proxy = MCPGatewayProxy(backend_server=backend_server, waf=waf)

    with waf.session(session_id="sess_mcp_1"):
        # Allowed MCP Tool call
        res1 = mcp_proxy.invoke_tool("fetch_file", {"path": "/docs/readme.txt", "max_kb": 100})
        print(f"▶ 1. Safe MCP Tool Call Execution: {res1}")

        # Blocked MCP Tool call (exceeds threshold)
        try:
            mcp_proxy.invoke_tool("fetch_file", {"path": "/data/dump.iso", "max_kb": 10240})
        except GuardWAFSecurityError as err:
            print(f"▶ 2. 🚨 BLOCKED MCP Tool Call Execution: {err}")

    print("=================================================================")

if __name__ == "__main__":
    main()
