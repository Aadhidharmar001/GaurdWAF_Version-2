"""
GuardWAF LangGraph State Graph Framework Integration Example.
Demonstrates securing LangGraph state node tool execution via LangGraphAdapter.
"""

import sys
import os

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from guardwaf import GuardWAF, GuardWAFSecurityError
from guardwaf.core.models import PolicyConfig, PolicyRules, BulkThresholdRule
from guardwaf.integrations.langgraph import protect_langgraph_tool

def execute_system_command(command: str, timeout_sec: int = 10):
    return {"status": "SUCCESS", "command": command, "output": "command output"}

def main():
    print("=================================================================")
    print("🛡️  GUARdWAF LANGGRAPH FRAMEWORK INTEGRATION DEMO")
    print("=================================================================")

    rules = PolicyRules(bulk_thresholds=[BulkThresholdRule(tool="sys_cmd", param_name="timeout_sec", max_value=30)])
    policy = PolicyConfig(metadata={"policy_name": "langgraph_policy"}, rules=rules)
    waf = GuardWAF(policy=policy, secret_key="langgraph_demo_secret_key_32bytes")

    protected_node_tool = protect_langgraph_tool(execute_system_command, waf=waf, tool_name="sys_cmd")

    with waf.session(session_id="sess_lg_1"):
        res1 = protected_node_tool(command="ls -la", timeout_sec=10)
        print(f"▶ 1. Safe LangGraph State Tool Execution: {res1}")

        try:
            protected_node_tool(command="sleep 100", timeout_sec=100)
        except GuardWAFSecurityError as err:
            print(f"▶ 2. 🚨 BLOCKED LangGraph State Tool Execution: {err}")

    print("=================================================================")

if __name__ == "__main__":
    main()
