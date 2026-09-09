"""
Real-World Customer Support AI Agent Integration Demonstration.
Governs 5 business tools: lookup_customer, view_orders, issue_refund, cancel_order, update_address.
Demonstrates safe calls (ALLOW), high-risk operations (HITL), and unauthorized actions (BLOCK).
Verifies invariant A: Downstream tool execution count = 0 on blocked actions.
"""

import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from guardwaf import GuardWAF, GuardWAFHITLRequiredError, GuardWAFSecurityError, protect
from guardwaf.control_plane.services.hitl_service import HITLWorkstationService
from guardwaf.core.models import (
    BulkThresholdRule,
    HITLRule,
    ParameterBlocklistRule,
    PolicyConfig,
    PolicyRules,
)

# Downstream tool counter verifying zero execution on block
execution_counters = {
    "lookup_customer": 0,
    "view_orders": 0,
    "issue_refund": 0,
    "cancel_order": 0,
    "update_address": 0,
}


def raw_lookup_customer(customer_id: str):
    execution_counters["lookup_customer"] += 1
    return {"customer_id": customer_id, "name": "Alice Smith", "plan": "enterprise"}


def raw_view_orders(customer_id: str):
    execution_counters["view_orders"] += 1
    return {"customer_id": customer_id, "orders": [{"id": "ord_101", "total": 150.0}]}


def raw_issue_refund(customer_id: str, amount: float):
    execution_counters["issue_refund"] += 1
    return {"status": "REFUNDED", "amount": amount, "customer_id": customer_id}


def raw_cancel_order(order_id: str):
    execution_counters["cancel_order"] += 1
    return {"status": "CANCELLED", "order_id": order_id}


def raw_update_address(customer_id: str, new_address: str):
    execution_counters["update_address"] += 1
    return {"status": "UPDATED", "address": new_address}


def main():
    print("==========================================================================================")
    print("🛡️  GUARdWAF REAL-WORLD CUSTOMER SUPPORT AGENT INTEGRATION")
    print("==========================================================================================")

    # 1. Policy Rules Configuration
    rules = PolicyRules(
        bulk_thresholds=[BulkThresholdRule(tool="issue_refund", param_name="amount", max_value=500.0)],
        hitl_rules=[HITLRule(tool="issue_refund", condition_param="amount", greater_than=100.0)],
        parameter_blocklist=[
            ParameterBlocklistRule(
                tool="cancel_order",
                param_name="order_id",
                blocklist=["SYSTEM_CRITICAL"],
            )
        ],
    )
    policy = PolicyConfig(metadata={"policy_name": "support_agent_policy"}, rules=rules)
    waf = GuardWAF(policy=policy, secret_key="real_support_demo_secret_key_32bytes_long")
    hitl_service = HITLWorkstationService(waf=waf)

    # Register tool bodies
    waf.register_tool("lookup_customer", raw_lookup_customer)
    waf.register_tool("view_orders", raw_view_orders)
    waf.register_tool("issue_refund", raw_issue_refund)
    waf.register_tool("cancel_order", raw_cancel_order)
    waf.register_tool("update_address", raw_update_address)

    # Decorate tools
    lookup_customer = protect(tool_name="lookup_customer", client=waf)(raw_lookup_customer)
    view_orders = protect(tool_name="view_orders", client=waf)(raw_view_orders)
    issue_refund = protect(tool_name="issue_refund", client=waf)(raw_issue_refund)
    cancel_order = protect(tool_name="cancel_order", client=waf)(raw_cancel_order)
    update_address = protect(tool_name="update_address", client=waf)(raw_update_address)

    with waf.session(session_id="sess_supp_1"):
        # 1. Safe Read: Lookup Customer (ALLOW)
        print("▶ 1. Customer Support Agent: Lookup Customer 'cust_404'...")
        res1 = lookup_customer(customer_id="cust_404")
        print(f"   ✅ ALLOWED: {res1}")

        # 2. Safe Read: View Orders (ALLOW)
        print("\n▶ 2. Customer Support Agent: View Customer Orders...")
        res2 = view_orders(customer_id="cust_404")
        print(f"   ✅ ALLOWED: {res2}")

        # 3. Small Refund ($45.00) (ALLOW)
        print("\n▶ 3. Customer Support Agent: Issue $45.00 Refund...")
        res3 = issue_refund(customer_id="cust_404", amount=45.0)
        print(f"   ✅ ALLOWED: {res3}")

        # 4. Large Refund ($250.00) (REQUIRE HITL)
        print("\n▶ 4. Customer Support Agent: Issue $250.00 Refund ➔ Triggers HITL...")
        pending_id = None
        try:
            issue_refund(customer_id="cust_404", amount=250.0)
        except GuardWAFHITLRequiredError as err:
            pending_id = err.pending_action_id
            print(f"   ⏸️ HITL SUSPENDED: Pending Action ID '{pending_id}'")

        # CISO Approves & Agent Resumes
        app_res = hitl_service.approve_action(
            organization_id="default",
            pending_action_id=pending_id,
            approver_id="ciso_admin",
        )
        token = app_res["approval_token"]
        res_resumed = waf.resume_sync(pending_action_id=pending_id, approval_token=token)
        print(f"   ✅ CISO Approved & Resumed Execution: {res_resumed}")

        # 5. Unauthorized Action (Cancel Critical System Order) (BLOCK)
        print("\n▶ 5. Customer Support Agent: Attempting Unauthorized Cancel System Order...")
        exec_before = execution_counters["cancel_order"]
        try:
            cancel_order(order_id="SYSTEM_CRITICAL_ORDER_99")
        except GuardWAFSecurityError as err:
            print(f"   🚨 GUARdWAF BLOCKED ACTION: {err}")

        exec_after = execution_counters["cancel_order"]
        print(f"   🔒 Downstream Executions Before: {exec_before}, After: {exec_after} (Delta: 0)")
        assert exec_before == exec_after

    print("==========================================================================================")
    print("✅ REAL-WORLD CUSTOMER SUPPORT AGENT INTEGRATION COMPLETE!")
    print("==========================================================================================")


if __name__ == "__main__":
    main()
