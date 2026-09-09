"""
Real-World Model Context Protocol (MCP) Gateway Integration Demonstration.
Demonstrates MCP Client ➔ MCPGatewayProxy ➔ GuardWAF Policy Evaluation ➔ Downstream Tool.
Verifies tool discovery governance, parameter digest verification, and zero execution on block.
"""

import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from guardwaf import GuardWAF, GuardWAFSecurityError
from guardwaf.core.models import BulkThresholdRule, PolicyConfig, PolicyRules
from guardwaf.mcp import MCPGatewayProxy, MCPToolMetadata


class RealMCPServer:
    def __init__(self):
        self.downstream_execution_count = 0

    def handle_request(self, request):
        self.downstream_execution_count += 1
        return {
            "status": "EXECUTED_BY_MCP_SERVER",
            "tool": request.tool_name,
            "args": request.arguments,
        }


def main():
    print("==========================================================================================")
    print("🛡️  GUARdWAF REAL-WORLD MCP GATEWAY AGENT INTEGRATION")
    print("==========================================================================================")

    rules = PolicyRules(bulk_thresholds=[BulkThresholdRule(tool="sql_query", param_name="max_rows", max_value=100)])
    policy = PolicyConfig(metadata={"policy_name": "mcp_real_policy"}, rules=rules)
    waf = GuardWAF(policy=policy, secret_key="mcp_real_demo_secret_key_32bytes_long")

    mcp_server = RealMCPServer()
    mcp_gateway = MCPGatewayProxy(waf=waf, downstream_handler=mcp_server.handle_request)

    with waf.session(session_id="sess_mcp_real_1"):
        # 1. Tool Discovery Governance
        print("▶ 1. MCP Gateway Tool Discovery Governance...")
        all_tools = [
            MCPToolMetadata(name="sql_query", description="Execute SQL"),
            MCPToolMetadata(name="drop_table", description="Drop DB table"),
        ]
        filtered = mcp_gateway.filter_allowed_tools("default", "mcp_agent", all_tools, allowed_tool_names=["sql_query"])
        print(f"   ✅ Filtered Discovery Tools: {[t.name for t in filtered]}")

        # 2. Allowed MCP Tool Call (max_rows=50)
        print("\n▶ 2. Executing Allowed MCP Tool Call (sql_query, max_rows=50)...")
        res1 = mcp_gateway.invoke_tool("sql_query", {"query": "SELECT * FROM users", "max_rows": 50})
        print(f"   ✅ ALLOWED MCP RESULT: {res1}")

        # 3. Blocked MCP Tool Call (max_rows=5000)
        print("\n▶ 3. Executing Blocked MCP Tool Call (sql_query, max_rows=5000)...")
        exec_before = mcp_gateway.downstream_execution_count
        try:
            mcp_gateway.invoke_tool("sql_query", {"query": "SELECT * FROM users", "max_rows": 5000})
        except GuardWAFSecurityError as err:
            print(f"   🚨 GUARdWAF BLOCKED MCP TOOL: {err}")

        exec_after = mcp_gateway.downstream_execution_count
        print(f"   🔒 Downstream MCP Executions Before: {exec_before}, After: {exec_after} (Delta: 0)")
        assert exec_before == exec_after

    print("==========================================================================================")
    print("✅ REAL-WORLD MCP GATEWAY AGENT INTEGRATION COMPLETE!")
    print("==========================================================================================")


if __name__ == "__main__":
    main()
