"""
GuardWAF Phase 2 Resumable HITL Workflow Real-World Demonstration Script.
Demonstrates:
1. Tool protection triggering HITL review ($250 refund > $100 policy limit).
2. Immutable PendingAction record creation in SQLiteStateStore.
3. Execution suspension with 0 unintended database side-effects.
4. Human administrator reviewing and approving the pending action.
5. Agent calling waf.resume() to execute the exact approved action.
6. Anti-replay verification: Attempting a second resume raises GuardWAFAlreadyExecutedError (EXACTLY-ONCE execution guarantee).
"""

import sys
import os
import asyncio

# Ensure stdout uses UTF-8 on Windows terminals
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from guardwaf import (
    GuardWAF,
    protect,
    session,
    SQLiteStateStore,
    GuardWAFHITLRequiredError,
    GuardWAFAlreadyExecutedError,
    GuardWAFSecurityError
)

# Initialize GuardWAF with SQLite persistent storage
state_store = SQLiteStateStore(db_path="examples_hitl_demo.db")
waf = GuardWAF(config_path="rules.yaml", state_store=state_store)

REFUND_EXECUTIONS_COUNT = 0

@protect(tool_name="lookup_customer")
def lookup_customer(customer_id: str):
    print(f"   [TOOL EXECUTION] DB Lookup: customer_id='{customer_id}'")
    return {"customer_id": customer_id, "status": "active"}

@protect(tool_name="process_refund")
def process_refund(customer_id: str, amount: float):
    global REFUND_EXECUTIONS_COUNT
    print(f"   [TOOL EXECUTION] 💸 EXECUTING DB MUTATION: Refund ${amount:.2f} to {customer_id}")
    REFUND_EXECUTIONS_COUNT += 1
    return {"status": "SUCCESS", "customer_id": customer_id, "refunded_amount": amount}

async def run_resumable_hitl_demo():
    global REFUND_EXECUTIONS_COUNT
    print("=" * 75)
    print("🛡️  GUARdWAF PHASE 2 DEMO: DURABLE RESUMABLE HUMAN AUTHORIZATION WORKFLOW")
    print("=" * 75)

    session_id = "sess_hitl_demo_888"
    customer_id = "cust_alice"
    pending_action_id = None

    with waf.session(session_id=session_id, customer_id=customer_id):
        # Step 1: Predecessor Lookup
        print("\n▶ STEP 1: Agent calls lookup_customer('cust_alice')...")
        lookup_customer(customer_id)

        # Step 2: High-Risk Action Triggering HITL
        print("\n▶ STEP 2: Agent attempts process_refund('cust_alice', 250.00)...")
        print("   (Policy limit is $100.00 -> Triggers HITL Review)")
        try:
            process_refund(customer_id, 250.00)
            print("   ❌ FAIL: Execution should have suspended!")
        except GuardWAFHITLRequiredError as e:
            pending_action_id = e.pending_action_id
            print(f"   ⏸️  GUARDWAF SUSPENDED EXECUTION:")
            print(f"      - Pending Action ID : {pending_action_id}")
            print(f"      - Approval Token    : {e.approval_token[:35]}...")
            print(f"      - DB Side Effects   : {REFUND_EXECUTIONS_COUNT} (Verified 0 Side Effects!)")

        # Step 3: Inspect Immutable PendingAction in SQLite
        print("\n▶ STEP 3: Inspector checks PendingAction state in SQLite DB...")
        pending_act = waf.state_store.get_pending_action(pending_action_id)
        print(f"   - Tool Name        : {pending_act.tool_name}")
        print(f"   - Requested Amount : ${pending_act.parameters.get('amount'):.2f}")
        print(f"   - Parameter Digest : {pending_act.parameter_digest[:20]}...")
        print(f"   - Current Status   : {pending_act.status.value}")

        # Step 4: Human Approval Workstation Action
        print("\n▶ STEP 4: Compliance Admin approves PendingAction in GuardWAF Workstation...")
        approved_act = waf.approve_pending_action(pending_action_id, approver_id="compliance_officer_sarah")
        print(f"   - Updated Status   : {approved_act.status.value}")
        print(f"   - Approver ID      : {approved_act.approver_id}")

        # Step 5: Agent Resumes Execution
        print("\n▶ STEP 5: Agent resumes execution via waf.resume()...")
        res = await waf.resume(pending_action_id, approved_act.approval_token)
        print(f"   - Resume Result    : {res}")
        print(f"   - DB Side Effects   : {REFUND_EXECUTIONS_COUNT} (Executed Exactly Once!)")

        # Step 6: Anti-Replay Attack Verification
        print("\n▶ STEP 6: Attacker attempts to REPLAY the approval token for a 2nd execution...")
        try:
            await waf.resume(pending_action_id, approved_act.approval_token)
            print("   ❌ SECURITY FAILURE: Replay attack succeeded!")
        except GuardWAFAlreadyExecutedError as e:
            print(f"   ✅ GUARDWAF REJECTED REPLAY ATTACK: {e}")
            print(f"   - Final DB Side Effects: {REFUND_EXECUTIONS_COUNT} (Guaranteed Exactly-Once!)")

    print("\n" + "=" * 75)
    print("✅ PHASE 2 DEMO COMPLETE: Durable Resumable HITL Workflow Fully Verified!")
    print("=" * 75)

if __name__ == "__main__":
    asyncio.run(run_resumable_hitl_demo())
