"""
Phase 10 Real-World Financial Agent Integration.
Governs tools: transfer_funds, check_balance.
Demonstrates Parameter Digest Verification, HITL Approval, Exactly-Once Resume, and Replay Prevention.
"""

import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from guardwaf import GuardWAF, GuardWAFHITLRequiredError, GuardWAFSecurityError, protect
from guardwaf.control_plane.services.hitl_service import HITLWorkstationService
from guardwaf.core.models import BulkThresholdRule, HITLRule, PolicyConfig, PolicyRules

execution_counters = {"transfer_funds": 0, "check_balance": 0}


def raw_transfer_funds(source_acc: str, dest_acc: str, amount: float):
    execution_counters["transfer_funds"] += 1
    return {
        "status": "TRANSFERRED",
        "from": source_acc,
        "to": dest_acc,
        "amount": amount,
    }


def main():
    print(
        "=========================================================================================="
    )
    print("🛡️  PHASE 10 REAL-WORLD FINANCIAL AGENT INTEGRATION")
    print(
        "=========================================================================================="
    )

    rules = PolicyRules(
        bulk_thresholds=[
            BulkThresholdRule(
                tool="transfer_funds", param_name="amount", max_value=10000.0
            )
        ],
        hitl_rules=[
            HITLRule(
                tool="transfer_funds", condition_param="amount", greater_than=1000.0
            )
        ],
    )
    waf = GuardWAF(
        policy=PolicyConfig(metadata={"policy_name": "fin"}, rules=rules),
        secret_key="fin_p10_secret_key_32bytes_long_min",
    )
    hitl_service = HITLWorkstationService(waf=waf)

    transfer_funds = protect(tool_name="transfer_funds", client=waf)(raw_transfer_funds)

    with waf.session(session_id="s_fin_10"):
        # 1. High-Value Transfer ($5000) -> Triggers HITL
        print("▶ 1. Transfer $5,000 (Triggers HITL)...")
        exec_before = execution_counters["transfer_funds"]
        p_id = None
        try:
            transfer_funds(source_acc="acc_1001", dest_acc="acc_9999", amount=5000.0)
        except GuardWAFHITLRequiredError as err:
            p_id = err.pending_action_id
            print(f"   ⏸️ HITL Suspended: Pending Action '{p_id}'")

        assert execution_counters["transfer_funds"] == exec_before
        print(
            f"   🔒 Executions Before Approval: {execution_counters['transfer_funds']} (Delta: 0)"
        )

        # 2. Approve & Resume
        tok = hitl_service.approve_action("default", p_id, "ciso_admin")[
            "approval_token"
        ]
        res = waf.resume_sync(p_id, tok)
        print(f"   ✅ Approved & Resumed: {res}")
        assert execution_counters["transfer_funds"] == exec_before + 1

        # 3. Replay Attempt -> 0 Executions
        print("\n▶ 2. Replaying Used Approval Token...")
        try:
            waf.resume_sync(p_id, tok)
        except GuardWAFSecurityError as err:
            print(f"   🚨 REPLAY BLOCKED: {err}")

        assert execution_counters["transfer_funds"] == exec_before + 1

    print(
        "=========================================================================================="
    )
    print("✅ FINANCIAL AGENT REAL-WORLD INTEGRATION COMPLETE!")
    print(
        "=========================================================================================="
    )


if __name__ == "__main__":
    main()
