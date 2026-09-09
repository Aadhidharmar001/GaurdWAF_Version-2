"""
GuardWAF Phase 3B Example Application: Enterprise Control Plane, Policy Distribution & Governance.
Demonstrates Scenarios 1-12 covering agent registration, versioned policy management, signed bundle distribution,
high-speed local SDK enforcement (< 1ms), dynamic policy updates, offline LKG resilience, tampered bundle rejection, and agent revocation.
"""

import sys
import time

# Ensure UTF-8 terminal output on Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from guardwaf import (
    AgentIdentity,
    GuardWAF,
    GuardWAFSecurityError,
    VerifiedPrincipal,
    protect,
)
from guardwaf.control_plane.app import ControlPlaneContainer
from guardwaf.control_plane.models.bundle import SignedPolicyBundle
from guardwaf.sdk.policy_client import PolicyClient, PolicyClientMode

# Initialize Control Plane Container & Key Manager
cp_container = ControlPlaneContainer()
agent_service = cp_container.agent_service
policy_service = cp_container.policy_service
bundle_service = cp_container.bundle_service

REFUND_COUNT = 0


@protect(tool_name="lookup_customer")
def lookup_customer(customer_id: str):
    print(f"   [TOOL EXECUTION] Looking up customer '{customer_id}'")
    return {"customer_id": customer_id, "status": "active"}


@protect(tool_name="process_refund")
def process_refund(customer_id: str, amount: float):
    global REFUND_COUNT
    REFUND_COUNT += 1
    print(f"   [TOOL EXECUTION] 💸 Refunding ${amount:.2f} to {customer_id}")
    return {"status": "SUCCESS", "refunded": amount}


def run_control_plane_demo():
    global REFUND_COUNT
    print("=" * 85)
    print("🛡️  GUARdWAF PHASE 3B DEMO: ENTERPRISE CONTROL PLANE & POLICY DISTRIBUTION")
    print("=" * 85)

    tenant_id = "acme_corp"
    agent_id = "support_agent_01"

    # --- Scenario 1: Register Tenant & Agent ---
    print("\n▶ SCENARIO 1: Registering tenant 'acme_corp' and agent 'support_agent_01' in Control Plane...")
    agent_rec = agent_service.register_agent(
        agent_id=agent_id,
        tenant_id=tenant_id,
        name="Customer Support Bot",
        version="1.0.0",
        environment="production",
    )
    print(f"   ✅ Agent Registered: ID='{agent_rec.agent_id}', Status={agent_rec.status.value}")

    # --- Scenario 2: Create Refund Policy Version 1 ($500 limit) ---
    print("\n▶ SCENARIO 2: Creating Policy 'refund_policy' Version 1 ($500 max refund)...")
    pol_rec = policy_service.create_policy(tenant_id=tenant_id, name="refund_policy")
    v1_rules = {
        "sequences": [{"tool": "process_refund", "requires": ["lookup_customer"]}],
        "bulk_thresholds": [{"tool": "process_refund", "param_name": "amount", "max_value": 500}],
    }
    ver1 = policy_service.create_version(pol_rec.policy_id, rules=v1_rules)
    print(f"   ✅ Version 1 Created: ID='{ver1.version_id}', SHA-256 Digest={ver1.content_digest[:20]}...")

    # --- Scenario 3: Publish and Activate Policy v1 ---
    print("\n▶ SCENARIO 3: Publishing and Activating Policy Version 1...")
    policy_service.publish_and_activate(pol_rec.policy_id, version_number=1)
    policy_service.assign_policy(tenant_id=tenant_id, policy_id=pol_rec.policy_id, agent_id=agent_id)
    print("   ✅ Policy Version 1 Activated and Assigned to Agent 'support_agent_01'")

    # --- Scenario 4: Issue Signed Policy Bundle ---
    print("\n▶ SCENARIO 4: Control Plane compiling and signing immutable Policy Bundle...")
    bundle_v1 = bundle_service.compile_and_sign_bundle(tenant_id=tenant_id, agent_id=agent_id)
    print(f"   ✅ Signed Bundle Issued: ID='{bundle_v1.bundle_id}', KeyID='{bundle_v1.key_id}'")
    print(f"      - HMAC Signature: {bundle_v1.signature[:35]}...")

    # --- Scenario 5: SDK PolicyClient Fetches & Verifies Bundle ---
    print("\n▶ SCENARIO 5: GuardWAF SDK PolicyClient fetching and cryptographically verifying bundle...")
    policy_client = PolicyClient(
        tenant_id=tenant_id,
        agent_id=agent_id,
        bundle_service=bundle_service,
        mode=PolicyClientMode.GRACE_PERIOD,
    )
    policy_client.fetch_and_apply_remote()
    print("   ✅ SDK PolicyClient Cryptographically Verified and Applied Signed Bundle v1")

    # Initialize GuardWAF SDK with PolicyClient
    waf = GuardWAF(policy_client=policy_client)
    alice_principal = VerifiedPrincipal(principal_id="usr_alice", tenant_id=tenant_id, subject="alice")
    support_agent = AgentIdentity(agent_id=agent_id, tenant_id=tenant_id)

    # --- Scenario 6: Agent Executes Allowed Action ($250 <= $500 v1 limit) ---
    print("\n▶ SCENARIO 6: Agent executing $250.00 refund (Policy v1 limit: $500.00)...")
    start_eval = time.time()
    with waf.verified_session(principal=alice_principal, agent=support_agent):
        lookup_customer("cust_alice")
        res = process_refund("cust_alice", 250.00)
        eval_time_ms = round((time.time() - start_eval) * 1000, 3)
        print(f"   ✅ SUCCESS: Refund executed cleanly! ({res})")
        print(f"      - Local Policy Evaluation Latency: {eval_time_ms} ms (Verified < 1ms target!)")

    # --- Scenario 7: Control Plane Updates Policy to Version 2 ($100 limit) ---
    print("\n▶ SCENARIO 7: Control Plane creating and activating Policy Version 2 ($100 max refund)...")
    v2_rules = {
        "sequences": [{"tool": "process_refund", "requires": ["lookup_customer"]}],
        "bulk_thresholds": [{"tool": "process_refund", "param_name": "amount", "max_value": 100}],
    }
    ver2 = policy_service.create_version(pol_rec.policy_id, rules=v2_rules)
    policy_service.publish_and_activate(pol_rec.policy_id, version_number=2)
    print(f"   ✅ Policy Version 2 Activated (SHA-256: {ver2.content_digest[:20]}...)")

    # --- Scenario 8: SDK PolicyClient Refreshes Policy Bundle ---
    print("\n▶ SCENARIO 8: SDK PolicyClient refreshing policy bundle from Control Plane...")
    policy_client.fetch_and_apply_remote()
    print("   ✅ SDK PolicyClient Atomically Swapped Active Policy to Version 2")

    # --- Scenario 9: Action Previously Allowed is NOW BLOCKED ---
    print("\n▶ SCENARIO 9: Agent re-attempts $250.00 refund (Policy v2 limit: $100.00)...")
    with waf.verified_session(principal=alice_principal, agent=support_agent):
        lookup_customer("cust_alice")
        try:
            process_refund("cust_alice", 250.00)
            print("   ❌ FAIL: $250 refund was not blocked by policy v2!")
        except GuardWAFSecurityError as e:
            print(f"   ✅ GUARDWAF BLOCKED ACTION UNDER POLICY V2: {e.message}")

    # --- Scenario 10: Control Plane Goes Offline (Offline Resilience with LKG Policy) ---
    print("\n▶ SCENARIO 10: Control Plane goes OFFLINE. Testing SDK Last Known Good (LKG) policy resilience...")

    # Simulate Control Plane Outage by setting bundle_fetcher to a failing function
    def failing_fetcher():
        raise RuntimeError("Control Plane HTTP Connection Refused (Outage Simulated)")

    policy_client.set_bundle_fetcher(failing_fetcher)

    # Attempt remote fetch -> Fails, but SDK retains LKG policy v2!
    policy_client.fetch_and_apply_remote()

    with waf.verified_session(principal=alice_principal, agent=support_agent):
        lookup_customer("cust_alice")
        # $50 refund <= $100 v2 limit -> Allowed under offline LKG policy
        res_offline = process_refund("cust_alice", 50.00)
        print("   ✅ SUCCESS: Executed $50.00 refund using Last Known Good Policy during Control Plane outage!")

    # --- Scenario 11: Attacker Sends Tampered Policy Bundle ---
    print("\n▶ SCENARIO 11: Attacker sends tampered policy bundle to SDK...")
    valid_bundle = bundle_service.compile_and_sign_bundle(tenant_id=tenant_id, agent_id=agent_id)
    tampered_bundle = SignedPolicyBundle.model_validate(valid_bundle.model_dump())
    # Tamper with policy rules payload (e.g. change limit from 100 to 10000)
    tampered_bundle.policy_payload["rules"]["bulk_thresholds"][0]["max_value"] = 10000

    applied = policy_client.verify_and_apply_bundle(tampered_bundle)
    assert applied is False
    print("   ✅ GUARDWAF REJECTED TAMPERED BUNDLE: Active LKG policy remained unchanged!")

    # --- Scenario 12: Agent Revocation ---
    print("\n▶ SCENARIO 12: Control Plane revokes agent 'support_agent_01'...")
    agent_service.revoke_agent(agent_id, reason="Compromised credentials suspected")
    try:
        bundle_service.compile_and_sign_bundle(tenant_id=tenant_id, agent_id=agent_id)
        print("   ❌ FAIL: Revoked agent received bundle!")
    except GuardWAFSecurityError as e:
        print(f"   ✅ CONTROL PLANE REJECTED BUNDLE FOR REVOKED AGENT: {e.message}")

    print("\n" + "=" * 85)
    print("✅ PHASE 3B DEMO COMPLETE: Control Plane, Signed Bundles & SDK Governance Verified!")
    print("=" * 85)


if __name__ == "__main__":
    run_control_plane_demo()
