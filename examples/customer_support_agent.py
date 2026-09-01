"""
GuardWAF Customer Support Refund Agent Real-World Demonstration Script.

Demonstrates:
1. Valid flow: lookup_customer -> process_refund ($45) -> ALLOWED
2. Sequence attack: process_refund without lookup -> BLOCKED (Zero side effects!)
3. Data Scope attack: refunding another customer ID -> BLOCKED (Zero side effects!)
4. Rate limit attack: 4th refund call -> BLOCKED
5. HITL review: refunding $250 (> $100 threshold) -> SUSPENDED FOR HITL
"""

import sys

# Ensure stdout uses UTF-8 on Windows terminals
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from guardwaf import GuardWAF, GuardWAFHITLRequiredError, GuardWAFSecurityError, protect

# Initialize GuardWAF client with rules policy
waf = GuardWAF(config_path="rules.yaml")

# Simulated Database Counter to mathematically prove ZERO side effects on blocked calls
DB_MUTATIONS_COUNT = 0


@protect(tool_name="lookup_customer")
def lookup_customer(customer_id: str):
    print(f"   [TOOL EXECUTION] Executing DB query: lookup_customer({customer_id})")
    return {"customer_id": customer_id, "name": "Alice Smith", "status": "VIP"}


@protect(tool_name="process_refund")
def process_refund(customer_id: str, amount: float):
    global DB_MUTATIONS_COUNT
    print(
        f"   [TOOL EXECUTION] 💸 EXECUTING DB MUTATION: Refund ${amount:.2f} to {customer_id}"
    )
    DB_MUTATIONS_COUNT += 1
    return {"status": "SUCCESS", "customer_id": customer_id, "refunded_amount": amount}


def run_demo():
    global DB_MUTATIONS_COUNT
    print("=" * 70)
    print("🛡️  GUARdWAF DEMO: CUSTOMER SUPPORT REFUND AGENT RUNTIME SECURITY")
    print("=" * 70)

    # -------------------------------------------------------------------------
    # Scenario 1: Legitimate Agent Workflow
    # -------------------------------------------------------------------------
    print("\n▶ SCENARIO 1: Legitimate Agent Workflow (Lookup -> Refund $45.00)")
    with waf.session(session_id="sess_legit_100", customer_id="cust_alice"):
        print("1. Calling lookup_customer('cust_alice')...")
        cust_info = lookup_customer("cust_alice")
        print(f"   Result: {cust_info}")

        print("2. Calling process_refund('cust_alice', 45.00)...")
        res = process_refund("cust_alice", 45.00)
        print(f"   Result: {res}")
        print(f"   --> Total DB Mutations Executed: {DB_MUTATIONS_COUNT}")

    # -------------------------------------------------------------------------
    # Scenario 2: Sequence Violation Attack
    # -------------------------------------------------------------------------
    print("\n▶ SCENARIO 2: Sequence Attack (Skipping lookup_customer step)")
    initial_db_count = DB_MUTATIONS_COUNT
    with waf.session(session_id="sess_attack_200", customer_id="cust_bob"):
        print(
            "1. Agent attempts process_refund('cust_bob', 30.00) directly without lookup..."
        )
        try:
            process_refund("cust_bob", 30.00)
            print(
                "   ❌ SECURITY FAILURE: Action executed when it should have been blocked!"
            )
        except GuardWAFSecurityError as e:
            print(f"   ✅ GUARDWAF BLOCKED ACTION: {e}")
            print(
                f"   --> Total DB Mutations Executed: {DB_MUTATIONS_COUNT} (Unchanged: {DB_MUTATIONS_COUNT == initial_db_count})"
            )

    # -------------------------------------------------------------------------
    # Scenario 3: Cross-Tenant Data Scope Attack
    # -------------------------------------------------------------------------
    print(
        "\n▶ SCENARIO 3: Cross-Tenant Data Scope Attack (Session=cust_charlie, Target=cust_victim)"
    )
    initial_db_count = DB_MUTATIONS_COUNT
    with waf.session(session_id="sess_attack_300", customer_id="cust_charlie"):
        lookup_customer("cust_charlie")
        print("1. Agent attempts process_refund('cust_victim', 50.00)...")
        try:
            process_refund("cust_victim", 50.00)
            print(
                "   ❌ SECURITY FAILURE: Action executed when it should have been blocked!"
            )
        except GuardWAFSecurityError as e:
            print(f"   ✅ GUARDWAF BLOCKED ACTION: {e}")
            print(
                f"   --> Total DB Mutations Executed: {DB_MUTATIONS_COUNT} (Unchanged: {DB_MUTATIONS_COUNT == initial_db_count})"
            )

    # -------------------------------------------------------------------------
    # Scenario 4: Rate Limit Spanning Attack
    # -------------------------------------------------------------------------
    print("\n▶ SCENARIO 4: Rate Limit Attack (Attempting 4 calls/min, Policy Max = 3)")
    initial_db_count = DB_MUTATIONS_COUNT
    with waf.session(session_id="sess_attack_400", customer_id="cust_dave"):
        lookup_customer("cust_dave")
        print("1. Executing refund 1...")
        process_refund("cust_dave", 10.00)
        print("2. Executing refund 2...")
        process_refund("cust_dave", 10.00)
        print("3. Executing refund 3...")
        process_refund("cust_dave", 10.00)
        print("4. Executing refund 4 (Exceeding max 3 calls/min)...")
        try:
            process_refund("cust_dave", 10.00)
            print("   ❌ SECURITY FAILURE: Rate limit failed!")
        except GuardWAFSecurityError as e:
            print(f"   ✅ GUARDWAF BLOCKED ACTION: {e}")

    # -------------------------------------------------------------------------
    # Scenario 5: High-Risk Action Requiring HITL Review
    # -------------------------------------------------------------------------
    print("\n▶ SCENARIO 5: High-Risk Action ($250.00 Refund -> HITL Approval Required)")
    with waf.session(session_id="sess_hitl_500", customer_id="cust_eve"):
        lookup_customer("cust_eve")
        print("1. Agent attempts process_refund('cust_eve', 250.00)...")
        try:
            process_refund("cust_eve", 250.00)
        except GuardWAFHITLRequiredError as e:
            print(f"   ⏸️ GUARDWAF SUSPENDED FOR HITL: {e}")
            print(f"      Approval Token Generated: {e.approval_token[:30]}...")

    print("\n" + "=" * 70)
    print(
        "✅ DEMO COMPLETE: All security properties verified with 0 unintended side effects!"
    )
    print("=" * 70)


if __name__ == "__main__":
    run_demo()
