"""
Phase 10 Real-World LangGraph Workflow Agent Integration.
Governs LangGraph state graph tool nodes using LangGraphAdapter.
Verifies state graph node protection and zero downstream node executions on block.
"""

import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from guardwaf import GuardWAF, GuardWAFSecurityError
from guardwaf.core.models import BulkThresholdRule, PolicyConfig, PolicyRules
from guardwaf.integrations.langgraph import protect_langgraph_tool

node_execution_counter = 0


def raw_deploy_cluster(cluster_name: str, replica_count: int):
    global node_execution_counter
    node_execution_counter += 1
    return {"status": "DEPLOYED", "cluster": cluster_name, "replicas": replica_count}


def main():
    print(
        "=========================================================================================="
    )
    print("🛡️  PHASE 10 REAL-WORLD LANGGRAPH WORKFLOW INTEGRATION")
    print(
        "=========================================================================================="
    )

    rules = PolicyRules(
        bulk_thresholds=[
            BulkThresholdRule(
                tool="deploy_cluster", param_name="replica_count", max_value=5
            )
        ]
    )
    waf = GuardWAF(
        policy=PolicyConfig(metadata={"policy_name": "lg_p10"}, rules=rules),
        secret_key="lg_p10_secret_key_32bytes_long_min_l",
    )

    deploy_node = protect_langgraph_tool(
        raw_deploy_cluster, waf=waf, tool_name="deploy_cluster"
    )

    with waf.session(session_id="s_lg_p10"):
        # 1. Allowed Node Step
        res1 = deploy_node(cluster_name="prod_api", replica_count=3)
        print(f"▶ 1. LangGraph Deploy Node (3 replicas): {res1}")

        # 2. Blocked Node Step -> 0 Executions
        print("\n▶ 2. LangGraph Deploy Node (50 replicas)...")
        exec_before = node_execution_counter
        try:
            deploy_node(cluster_name="prod_api", replica_count=50)
        except GuardWAFSecurityError as err:
            print(f"   🚨 BLOCKED LANGGRAPH NODE: {err}")

        exec_after = node_execution_counter
        assert exec_before == exec_after
        print(f"   🔒 Downstream Node Executions After Block: {exec_after} (Delta: 0)")

    print(
        "=========================================================================================="
    )
    print("✅ LANGGRAPH WORKFLOW REAL-WORLD INTEGRATION COMPLETE!")
    print(
        "=========================================================================================="
    )


if __name__ == "__main__":
    main()
