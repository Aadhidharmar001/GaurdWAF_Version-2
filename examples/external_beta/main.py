"""
GuardWAF External Beta Starter Project.
Minimal, copy-paste starter project for external developers testing GuardWAF.
Demonstrates: Allowed Call ($25) ➔ HITL Call ($75) ➔ Blocked Call ($500).
"""

import sys
import os

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from guardwaf import GuardWAF, protect, GuardWAFSecurityError, GuardWAFHITLRequiredError

def raw_send_payment(recipient: str, amount: float):
    return {"status": "PAID", "recipient": recipient, "amount": amount}

def main():
    print("==========================================================================================")
    print("🛡️  GUARdWAF EXTERNAL BETA STARTER PROJECT")
    print("==========================================================================================")

    policy_path = os.path.join(os.path.dirname(__file__), "policy.yaml")
    waf = GuardWAF(policy_path=policy_path, secret_key="beta_starter_secret_key_32bytes_long")

    send_payment = protect(tool_name="send_payment", client=waf)(raw_send_payment)

    with waf.session(session_id="beta_sess_1"):
        # 1. Allowed Call ($25.00)
        print("▶ 1. Sending $25.00 Payment (Allowed)...")
        res1 = send_payment(recipient="alice@example.com", amount=25.0)
        print(f"   ✅ ALLOWED: {res1}")

        # 2. HITL Call ($75.00)
        print("\n▶ 2. Sending $75.00 Payment (Triggers HITL)...")
        try:
            send_payment(recipient="bob@example.com", amount=75.0)
        except GuardWAFHITLRequiredError as err:
            print(f"   ⏸️ HITL SUSPENDED: Action ID '{err.pending_action_id}' (Requires Approval)")

        # 3. Blocked Call ($500.00)
        print("\n▶ 3. Sending $500.00 Payment (Exceeds Policy Max $100)...")
        try:
            send_payment(recipient="charlie@example.com", amount=500.0)
        except GuardWAFSecurityError as err:
            print(f"   🚨 GUARdWAF BLOCKED ACTION: {err}")

    print("==========================================================================================")
    print("✅ STARTER PROJECT COMPLETE! You successfully protected your first AI tool.")
    print("==========================================================================================")

if __name__ == "__main__":
    main()
