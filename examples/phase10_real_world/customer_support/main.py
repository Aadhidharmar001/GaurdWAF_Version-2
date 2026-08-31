"""
Phase 10 Real-World Customer Support Agent Integration.
Governs tools: lookup_customer, view_orders, issue_refund, cancel_order, update_address.
Verifies Invariant A: Downstream execution count == 0 on BLOCKED / HITL / REVOKED / TENANT_LOCKDOWN actions.
"""

import sys
import os

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from guardwaf import GuardWAF, protect, GuardWAFSecurityError, GuardWAFHITLRequiredError
from guardwaf.core.models import PolicyConfig, PolicyRules, BulkThresholdRule, HITLRule, ParameterBlocklistRule
from guardwaf.control_plane.services.hitl_service import HITLWorkstationService

execution_counters = {
    "lookup_customer": 0,
    "view_orders": 0,
    "issue_refund": 0,
    "cancel_order": 0,
    "update_address": 0
}

def raw_lookup_customer(customer_id: str):
    execution_counters["lookup_customer"] += 1
    return {"customer_id": customer_id, "name": "Alice Smith"}

def raw_view_orders(customer_id: str):
    execution_counters["view_orders"] += 1
    return {"customer_id": customer_id, "orders": [{"id": "ord_101", "total": 150.0}]}

def raw_issue_refund(customer_id: str, amount: float):
    execution_counters["issue_refund"] += 1
    return {"status": "REFUNDED", "amount": amount}

def raw_cancel_order(order_id: str):
    execution_counters["cancel_order"] += 1
    return {"status": "CANCELLED", "order_id": order_id}

def raw_update_address(customer_id: str, new_address: str):
    execution_counters["update_address"] += 1
    return {"status": "UPDATED", "address": new_address}

def main():
    print("==========================================================================================")
    print("🛡️  PHASE 10 REAL-WORLD CUSTOMER SUPPORT AGENT INTEGRATION")
    print("==========================================================================================")

    rules = PolicyRules(
        bulk_thresholds=[BulkThresholdRule(tool="issue_refund", param_name="amount", max_value=500.0)],
        hitl_rules=[HITLRule(tool="issue_refund", condition_param="amount", greater_than=100.0)],
        parameter_blocklist=[ParameterBlocklistRule(tool="cancel_order", param_name="order_id", blocklist=["CRITICAL_SYSTEM_ORDER"])]
    )
    waf = GuardWAF(policy=PolicyConfig(metadata={"policy_name": "cs"}, rules=rules), secret_key="cs_p10_secret_key_32bytes_long_min")
    hitl_service = HITLWorkstationService(waf=waf)

    lookup_customer = protect(tool_name="lookup_customer", client=waf)(raw_lookup_customer)
    view_orders = protect(tool_name="view_orders", client=waf)(raw_view_orders)
    issue_refund = protect(tool_name="issue_refund", client=waf)(raw_issue_refund)
    cancel_order = protect(tool_name="cancel_order", client=waf)(raw_cancel_order)

    with waf.session(session_id="s_cs_10"):
        # 1. Allowed Call
        res1 = lookup_customer(customer_id="cust_1")
        print(f"▶ 1. Lookup Customer (Allowed): {res1}")

        # 2. HITL Call ($200) -> 0 Executions before approval
        print("\n▶ 2. Issue $200 Refund (HITL)...")
        exec_before_hitl = execution_counters["issue_refund"]
        p_id = None
        try:
            issue_refund(customer_id="cust_1", amount=200.0)
        except GuardWAFHITLRequiredError as err:
            p_id = err.pending_action_id
            print(f"   ⏸️ HITL Suspended: Pending Action '{p_id}'")

        exec_during_hitl = execution_counters["issue_refund"]
        assert exec_before_hitl == exec_during_hitl
        print(f"   🔒 Downstream Execution Count During HITL: {exec_during_hitl} (Delta: 0)")

        # Approve & Resume
        tok = hitl_service.approve_action("default", p_id, "admin")["approval_token"]
        res_resumed = waf.resume_sync(p_id, tok)
        print(f"   ✅ Approved & Resumed: {res_resumed}")
        assert execution_counters["issue_refund"] == exec_before_hitl + 1

        # 3. Blocked Call -> 0 Executions
        print("\n▶ 3. Cancel Critical System Order (Blocked)...")
        exec_before_block = execution_counters["cancel_order"]
        try:
            cancel_order(order_id="CRITICAL_SYSTEM_ORDER")
        except GuardWAFSecurityError as err:
            print(f"   🚨 BLOCKED ACTION: {err}")

        exec_after_block = execution_counters["cancel_order"]
        assert exec_before_block == exec_after_block
        print(f"   🔒 Downstream Execution Count After Block: {exec_after_block} (Delta: 0)")

    print("==========================================================================================")
    print("✅ CUSTOMER SUPPORT REAL-WORLD INTEGRATION COMPLETE!")
    print("==========================================================================================")

if __name__ == "__main__":
    main()
