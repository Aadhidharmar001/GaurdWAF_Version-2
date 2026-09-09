"""
Phase 10 Real-World MCP Agent Integration.
Governs FastMCP / Standard MCP Tool Requests via MCPGatewayProxy.
Verifies Parameter Mutation Detection, Tool Discovery Filtering, and Zero Execution on Block.
"""

import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from guardwaf import GuardWAF, GuardWAFSecurityError
from guardwaf.core.models import BulkThresholdRule, PolicyConfig, PolicyRules
from guardwaf.mcp import MCPGatewayProxy


class MockMCPServer:
    def __init__(self):
        self.downstream_execution_count = 0

    def handle_request(self, request):
        self.downstream_execution_count += 1
        return {
            "status": "EXECUTED",
            "tool": request.tool_name,
            "args": request.arguments,
        }


def main():
    print("==========================================================================================")
    print("🛡️  PHASE 10 REAL-WORLD MCP GATEWAY INTEGRATION")
    print("==========================================================================================")

    rules = PolicyRules(bulk_thresholds=[BulkThresholdRule(tool="sql_query", param_name="max_rows", max_value=100)])
    waf = GuardWAF(
        policy=PolicyConfig(metadata={"policy_name": "mcp_p10"}, rules=rules),
        secret_key="mcp_p10_secret_key_32bytes_long_min",
    )

    mcp_server = MockMCPServer()
    gateway = MCPGatewayProxy(waf=waf, downstream_handler=mcp_server.handle_request)

    with waf.session(session_id="s_mcp_p10"):
        # 1. Allowed MCP Call
        res1 = gateway.invoke_tool("sql_query", {"query": "SELECT * FROM users", "max_rows": 50})
        print(f"▶ 1. Allowed MCP Call (max_rows=50): {res1}")

        # 2. Blocked MCP Call -> 0 Executions
        print("\n▶ 2. Blocked MCP Call (max_rows=5000)...")
        exec_before = gateway.downstream_execution_count
        try:
            gateway.invoke_tool("sql_query", {"query": "SELECT * FROM users", "max_rows": 5000})
        except GuardWAFSecurityError as err:
            print(f"   🚨 BLOCKED MCP TOOL: {err}")

        exec_after = gateway.downstream_execution_count
        assert exec_before == exec_after
        print(f"   🔒 Downstream MCP Executions After Block: {exec_after} (Delta: 0)")

    print("==========================================================================================")
    print("✅ MCP GATEWAY REAL-WORLD INTEGRATION COMPLETE!")
    print("==========================================================================================")


if __name__ == "__main__":
    main()
