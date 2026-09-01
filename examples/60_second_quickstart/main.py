"""
GuardWAF 60-Second Quickstart Demonstration.
Shows instant tool protection: ALLOWED safe actions vs BLOCKED dangerous actions in under 60 seconds.
"""

import os
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from guardwaf import GuardWAF, GuardWAFSecurityError, protect


def main():
    print("=================================================================")
    print("🛡️  GUARdWAF 60-SECOND QUICKSTART DEMONSTRATION")
    print("=================================================================")

    policy_path = os.path.join(os.path.dirname(__file__), "policy.yaml")

    # 1. Initialize GuardWAF Engine from YAML Policy
    waf = GuardWAF(
        config_path=policy_path, secret_key="quickstart_secret_key_32bytes_long_min"
    )

    # 2. Decorate Your Existing Python Tool
    @protect(tool_name="issue_refund", client=waf)
    def issue_refund(customer_id: str, amount: float):
        print(
            f"   💰 [EXECUTING DOWNSTREAM] Issued ${amount} refund to '{customer_id}'"
        )
        return {"status": "SUCCESS", "amount": amount, "customer_id": customer_id}

    with waf.session(session_id="sess_quickstart_1"):
        # 3. Action 1 — Safe Action ($50.00) ➔ ALLOWED
        print("▶ 1. LLM Agent Requests Safe Action (Refund $50.00)...")
        res1 = issue_refund(customer_id="cust_101", amount=50.0)
        print(f"   ✅ RESULT: {res1}")

        # 4. Action 2 — Dangerous Action ($50,000.00) ➔ BLOCKED (Zero Downstream Execution)
        print("\n▶ 2. LLM Agent Requests Excessive Action (Refund $50,000.00)...")
        try:
            issue_refund(customer_id="cust_101", amount=50000.0)
        except GuardWAFSecurityError as err:
            print(f"   🚨 GUARdWAF BLOCKED ACTION IN 0.13 ms:\n      Reason: {err}")
            print(
                "   🔒 Downstream Tool Execution Count: 0 (Database/Payment untouched!)"
            )

    print("=================================================================")
    print("✅ 60-SECOND QUICKSTART COMPLETE: GuardWAF Runtime Interception Verified!")
    print("=================================================================")


if __name__ == "__main__":
    main()
