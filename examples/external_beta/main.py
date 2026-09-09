"""
GuardWAF External Beta Starter Project.
Minimal, portable starter project for external developers testing GuardWAF.
Demonstrates:
  1. Allowed Call ($25.00) -> Downstream Tool Executes
  2. Blocked Call ($500.00) -> GuardWAF Intercepts -> ZERO Downstream Execution
  3. HITL Suspended Call ($75.00) -> Action Suspended for Human Approval
"""

import os
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Allow running directly from repository clone or as an installed package
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from guardwaf import GuardWAF, GuardWAFHITLRequiredError, GuardWAFSecurityError, protect

# Execution counter to verify the core security guarantee
EXECUTION_STATS = {"downstream_executions": 0}


def raw_send_payment(recipient: str, amount: float):
    """Downstream backend tool that would send real money or mutate a database."""
    EXECUTION_STATS["downstream_executions"] += 1
    return {"status": "PAID", "recipient": recipient, "amount": amount}


def main():
    print("=" * 80)
    print("🛡️  GUARDWAF EXTERNAL BETA STARTER PROJECT")
    print("=" * 80)

    policy_path = os.path.join(os.path.dirname(__file__), "policy.yaml")
    waf = GuardWAF(policy_path=policy_path, secret_key="beta_starter_secret_key_32bytes_long")

    # Protect the downstream tool body with GuardWAF
    send_payment = protect(tool_name="send_payment", client=waf)(raw_send_payment)

    with waf.session(session_id="beta_sess_1"):
        # -------------------------------------------------------------
        # Scenario 1: Allowed Action ($25.00 <= $50 threshold)
        # -------------------------------------------------------------
        print("\n▶ 1. Sending $25.00 Payment (Allowed by Policy)...")
        res1 = send_payment(recipient="alice@example.com", amount=25.0)
        print(f"   ✅ ALLOWED: {res1}")
        print(f"   Downstream Execution Count: {EXECUTION_STATS['downstream_executions']}")
        assert EXECUTION_STATS["downstream_executions"] == 1

        # -------------------------------------------------------------
        # Scenario 2: Blocked Action ($500.00 > $100 policy maximum)
        # -------------------------------------------------------------
        print("\n▶ 2. Sending $500.00 Payment (Exceeds Policy Maximum of $100.00)...")
        try:
            send_payment(recipient="charlie@example.com", amount=500.0)
            print("   ❌ FAILED: Blocked action executed!")
        except GuardWAFSecurityError as err:
            print(f"   🚨 BLOCKED ACTION INTERCEPTED: {err}")
            print(f"   Downstream Execution Count: {EXECUTION_STATS['downstream_executions']} (UNCHANGED)")

        # Verify the security invariant
        assert EXECUTION_STATS["downstream_executions"] == 1, "Blocked action must have ZERO downstream execution!"
        print("   🔒 GUARANTEE CONFIRMED: Downstream tool was NEVER entered on blocked call.")

        # -------------------------------------------------------------
        # Scenario 3: Human-in-the-Loop Suspended Action ($75.00 > $50)
        # -------------------------------------------------------------
        print("\n▶ 3. Sending $75.00 Payment (Requires Human-in-the-Loop Approval)...")
        try:
            send_payment(recipient="bob@example.com", amount=75.0)
            print("   ❌ FAILED: Unapproved HITL action executed!")
        except GuardWAFHITLRequiredError as err:
            print(f"   ⏸️  HITL SUSPENDED: Action ID '{err.pending_action_id}' requires HMAC approval.")
            print(f"   Downstream Execution Count: {EXECUTION_STATS['downstream_executions']} (UNCHANGED)")

        assert EXECUTION_STATS["downstream_executions"] == 1

    print("\n" + "=" * 80)
    print("✅ ALL TESTS PASSED! GuardWAF successfully protected your AI agent tools.")
    print("   Total Downstream Executions: 1 (Only the single allowed action ran)")
    print("=" * 80)


if __name__ == "__main__":
    main()
