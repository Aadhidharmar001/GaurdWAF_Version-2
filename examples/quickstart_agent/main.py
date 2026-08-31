"""
GuardWAF External Developer Quickstart Agent Example.
Demonstrates sub-15 minute integration: Install ➔ Configure ➔ Protect ➔ Execute.
"""

import sys
from guardwaf import GuardWAF, protect, GuardWAFSecurityError
from guardwaf.core.models import PolicyConfig, PolicyRules, BulkThresholdRule

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# 1. Configure GuardWAF Engine
rules = PolicyRules(
    bulk_thresholds=[
        BulkThresholdRule(tool="process_payment", param_name="amount", max_value=500.0)
    ]
)
policy = PolicyConfig(metadata={"policy_name": "developer_quickstart_policy"}, rules=rules)
waf = GuardWAF(policy=policy, secret_key="quickstart_dev_secret_key_32bytes_long")

# 2. Protect AI Agent Tool
@protect(tool_name="process_payment", client=waf)
def process_payment(customer_id: str, amount: float) -> str:
    # Target function body only executes if GuardWAF authorizes the action
    return f"Payment of ${amount:.2f} processed for {customer_id}."

def main():
    print("=================================================================")
    print("🛡️  GUARdWAF EXTERNAL DEVELOPER QUICKSTART AGENT")
    print("=================================================================")

    with waf.session(session_id="sess_quickstart_1", tenant_id="org_quickstart"):
        # 1. Allowed Call ($50.00)
        res_ok = process_payment(customer_id="cust_001", amount=50.0)
        print(f"✅ ALLOWED TOOL CALL: {res_ok}")

        # 2. Blocked Call ($1,200.00 > $500.00 threshold)
        try:
            process_payment(customer_id="cust_001", amount=1200.0)
            print("❌ FAIL: Policy violation was allowed!")
        except GuardWAFSecurityError as err:
            print(f"✅ BLOCKED POLICY VIOLATION: {err}")

    print("=================================================================")
    print("✅ QUICKSTART COMPLETE: GuardWAF Integration Working Successfully!")
    print("=================================================================")

if __name__ == "__main__":
    main()
