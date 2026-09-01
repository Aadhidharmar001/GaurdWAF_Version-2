"""
Real-World LangGraph Agent Workflow Integration Demonstration.
Demonstrates securing LangGraph state graph nodes via LangGraphAdapter.
User Request ➔ LangGraph State ➔ Agent Decision ➔ Tool Selection ➔ GuardWAF Enforcement ➔ Graph Continues Safely.
"""

import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from guardwaf import GuardWAF, GuardWAFSecurityError
from guardwaf.core.models import BulkThresholdRule, PolicyConfig, PolicyRules
from guardwaf.integrations.langgraph import protect_langgraph_tool

node_execution_counter = 0


def state_graph_deploy_service(service_name: str, replica_count: int):
    global node_execution_counter
    node_execution_counter += 1
    return {"status": "DEPLOYED", "service": service_name, "replicas": replica_count}


def main():
    print(
        "=========================================================================================="
    )
    print("🛡️  GUARdWAF REAL-WORLD LANGGRAPH WORKFLOW AGENT INTEGRATION")
    print(
        "=========================================================================================="
    )

    rules = PolicyRules(
        bulk_thresholds=[
            BulkThresholdRule(
                tool="deploy_service", param_name="replica_count", max_value=10
            )
        ]
    )
    policy = PolicyConfig(
        metadata={"policy_name": "langgraph_real_policy"}, rules=rules
    )
    waf = GuardWAF(policy=policy, secret_key="langgraph_real_secret_key_32bytes_l")

    protected_deploy_node = protect_langgraph_tool(
        state_graph_deploy_service, waf=waf, tool_name="deploy_service"
    )

    with waf.session(session_id="sess_lg_real_1"):
        # 1. State Graph Step 1: Deploy 3 replicas (ALLOW)
        print("▶ 1. LangGraph Workflow Node: Deploying 3 replicas...")
        res1 = protected_deploy_node(service_name="payment_api", replica_count=3)
        print(f"   ✅ ALLOWED LANGGRAPH NODE: {res1}")

        # 2. State Graph Step 2: Deploy 100 replicas (BLOCK)
        print(
            "\n▶ 2. LangGraph Workflow Node: Deploying 100 replicas (Exceeds Policy)..."
        )
        exec_before = node_execution_counter
        try:
            protected_deploy_node(service_name="payment_api", replica_count=100)
        except GuardWAFSecurityError as err:
            print(f"   🚨 GUARdWAF BLOCKED LANGGRAPH NODE: {err}")

        exec_after = node_execution_counter
        print(
            f"   🔒 Downstream Node Executions Before: {exec_before}, After: {exec_after} (Delta: 0)"
        )
        assert exec_before == exec_after

    print(
        "=========================================================================================="
    )
    print("✅ REAL-WORLD LANGGRAPH WORKFLOW AGENT INTEGRATION COMPLETE!")
    print(
        "=========================================================================================="
    )


if __name__ == "__main__":
    main()
