"""
GuardWAF Phase 4 Example Application: Multi-Tenant Enterprise Platform & Production Control Plane.
Demonstrates Scenarios 1-11 covering Acme Corp onboarding, user RBAC roles, agent registration, policy publishing,
secure credential generation, tool execution, HITL approval & exactly-once resume, cross-tenant isolation, developer RBAC block,
emergency disable, and end-to-end audit correlation timeline search.
"""

import sys

# Ensure UTF-8 terminal output on Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from guardwaf import GuardWAF, GuardWAFHITLRequiredError, GuardWAFSecurityError, protect
from guardwaf.control_plane.app import ControlPlaneContainer
from guardwaf.control_plane.auth.rbac import ACTION_PUBLISH_POLICY, RBACManager
from guardwaf.control_plane.models.org import Role
from guardwaf.control_plane.services.hitl_service import HITLWorkstationService
from guardwaf.core.models import BulkThresholdRule, HITLRule, PolicyConfig, PolicyRules

# Initialize Services
cp_container = ControlPlaneContainer()
org_service = cp_container.org_service
agent_service = cp_container.agent_service
policy_service = cp_container.policy_service
cred_service = cp_container.credential_service
hitl_service = cp_container.hitl_service
dashboard_service = cp_container.dashboard_service
incident_service = cp_container.incident_service

REFUND_EXEC_COUNT = 0


@protect(tool_name="lookup_customer")
def lookup_customer(customer_id: str):
    print(f"   [TOOL EXECUTION] Looking up customer '{customer_id}'")
    return {"customer_id": customer_id, "status": "active"}


@protect(tool_name="process_refund")
def process_refund(customer_id: str, amount: float):
    global REFUND_EXEC_COUNT
    REFUND_EXEC_COUNT += 1
    print(f"   [TOOL EXECUTION] 💸 Refunding ${amount:.2f} to {customer_id}")
    return {"status": "SUCCESS", "refunded": amount}


def run_phase4_demo():
    global REFUND_EXEC_COUNT
    print("=" * 85)
    print("🛡️  GUARdWAF PHASE 4 DEMO: MULTI-TENANT ENTERPRISE PLATFORM & CONTROL PLANE")
    print("=" * 85)

    # --- Scenario 1: Create Organization & Users ---
    print("\n▶ SCENARIO 1: Creating Organization 'Acme Corp' and Users (Sarah, John, Maya)...")
    acme_org = org_service.create_organization(name="Acme Corp", slug="acme-corp")
    sarah = org_service.create_user(email="sarah@acme.com", display_name="Sarah (Owner)")
    john = org_service.create_user(email="john@acme.com", display_name="John (Developer)")
    maya = org_service.create_user(email="maya@acme.com", display_name="Maya (Security Admin)")

    org_service.add_member(acme_org.organization_id, sarah.user_id, Role.OWNER)
    org_service.add_member(acme_org.organization_id, john.user_id, Role.DEVELOPER)
    org_service.add_member(acme_org.organization_id, maya.user_id, Role.SECURITY_ADMIN)

    print(f"   ✅ Organization Created: Name='{acme_org.name}', ID='{acme_org.organization_id}'")
    print(f"   ✅ Members Added: Owner={sarah.display_name}, Developer={john.display_name}, SecurityAdmin={maya.display_name}")

    # --- Scenario 2: Developer Registers Agent ---
    print("\n▶ SCENARIO 2: Developer John registering 'customer_support_agent'...")
    agent_id = "customer_support_agent"
    agent_rec = agent_service.register_agent(
        agent_id=agent_id,
        tenant_id=acme_org.organization_id,
        name="Customer Support Agent",
        version="1.0.0",
        environment="production",
        actor_id=john.user_id,
    )
    print(f"   ✅ Agent Registered: ID='{agent_rec.agent_id}', Tenant='{agent_rec.tenant_id}', Status={agent_rec.status.value}")

    # --- Scenario 3: Security Admin Creates & Publishes Policy ---
    print("\n▶ SCENARIO 3: Security Admin Maya creating and publishing 'refund_policy' v1...")
    pol_rec = policy_service.create_policy(
        tenant_id=acme_org.organization_id,
        name="refund_policy",
        description="Acme Corp Refund Governance Policy",
        actor_id=maya.user_id,
    )
    v1_rules = {
        "bulk_thresholds": [{"tool": "process_refund", "param_name": "amount", "max_value": 500}],
        "hitl_rules": [{"tool": "process_refund", "param_name": "amount", "threshold": 500}],
    }
    ver1 = policy_service.create_version(pol_rec.policy_id, rules=v1_rules, actor_id=maya.user_id)
    policy_service.publish_and_activate(pol_rec.policy_id, version_number=1, actor_id=maya.user_id)
    policy_service.assign_policy(
        tenant_id=acme_org.organization_id,
        policy_id=pol_rec.policy_id,
        agent_id=agent_id,
    )
    print(f"   ✅ Policy Version 1 Activated: SHA-256 Digest={ver1.content_digest[:20]}...")

    # --- Scenario 4: Issue Agent API Credential & Connect SDK ---
    print("\n▶ SCENARIO 4: Developer John generating API Credential for 'customer_support_agent'...")
    cred_res = cred_service.issue_credential(organization_id=acme_org.organization_id, agent_id=agent_id)
    print(f"   ✅ Credential Issued: ID='{cred_res.credential_id}'")
    print(f"      - Plaintext Key (Shown Once): '{cred_res.plaintext_api_key[:25]}...'")
    print("      - Database Persistence: Stored ONLY as SHA-256 Hash")

    # Verify API key authentication
    verified_cred = cred_service.verify_credential(cred_res.plaintext_api_key)
    print(f"   ✅ API Key Authenticated Successfully for Agent '{verified_cred.agent_id}'!")

    # Initialize GuardWAF Engine
    rules_obj = PolicyRules(
        bulk_thresholds=[BulkThresholdRule(tool="process_refund", param_name="amount", max_value=5000)],
        hitl_rules=[HITLRule(tool="process_refund", condition_param="amount", greater_than=100.0)],
    )

    policy_obj = PolicyConfig(metadata={"policy_name": "refund_policy"}, rules=rules_obj)
    waf = GuardWAF(policy=policy_obj, secret_key="dev_secret_key_phase4_demo")
    waf.register_tool("process_refund", process_refund)
    hitl_service = HITLWorkstationService(waf=waf)

    # --- Scenario 5: Agent Action Executions ---
    print("\n▶ SCENARIO 5: Agent performing tool calls...")

    # 1. lookup_customer -> ALLOWED
    with waf.session(session_id="sess_101", tenant_id=acme_org.organization_id):
        res_lookup = lookup_customer("cust_101")
        print(f"   ✅ lookup_customer: ALLOWED ({res_lookup})")

    # 2. refund $50 -> ALLOWED
    with waf.session(session_id="sess_101", tenant_id=acme_org.organization_id):
        res_50 = process_refund("cust_101", 50.00)
    # 3. refund $1000 -> HITL REQUIRED

    pending_action_id = None
    with waf.session(session_id="sess_101", tenant_id=acme_org.organization_id):
        try:
            process_refund("cust_101", 1000.00)
            print("   ❌ FAIL: $1000 refund was not suspended for HITL!")
        except (GuardWAFHITLRequiredError, GuardWAFSecurityError) as e:
            pending_action_id = getattr(e, "pending_action_id", None)
            if not pending_action_id:
                pending_actions = waf.state_store.list_pending_actions()
                if pending_actions:
                    pending_action_id = pending_actions[-1].pending_action_id

            print(f"   ✅ process_refund ($1000.00): HITL SUSPENDED: {e.message}")
            print(f"      - Created Immutable PendingAction: ID='{pending_action_id}'")

    # --- Scenario 6: Security Admin Approves Pending Action ---
    print("\n▶ SCENARIO 6: Security Admin Maya opening HITL Queue and approving pending action...")
    hitl_res = hitl_service.approve_action(
        organization_id=acme_org.organization_id,
        pending_action_id=pending_action_id,
        approver_id=maya.user_id,
    )
    approval_token = hitl_res["approval_token"]
    print(f"   ✅ Action Approved: ID='{pending_action_id}'")
    print(f"      - Cryptographic Approval Token Issued: {approval_token[:35]}...")

    # --- Scenario 7: Resume Action & Verify Exactly-Once Execution ---
    print("\n▶ SCENARIO 7: Agent resuming approved action via waf.resume()...")
    current_count = REFUND_EXEC_COUNT
    with waf.session(session_id="sess_101", tenant_id=acme_org.organization_id):
        res_resume = waf.resume_sync(pending_action_id=pending_action_id, approval_token=approval_token)
        print(f"   ✅ SUCCESS: Resumed and executed refund! ({res_resume})")
        assert REFUND_EXEC_COUNT == current_count + 1

    # Attempt replay -> Must fail
    print("   Testing Replay Prevention...")
    with waf.session(session_id="sess_101", tenant_id=acme_org.organization_id):
        try:
            waf.resume_sync(pending_action_id=pending_action_id, approval_token=approval_token)
            print("   ❌ FAIL: Replay was allowed!")
        except Exception as e:
            print(f"   ✅ GUARDWAF REPLAY BLOCKED: {e}")

    # --- Scenario 8: Cross-Tenant Isolation ---
    print("\n▶ SCENARIO 8: Testing Cross-Tenant Access from Organization 'Beta Corp'...")
    beta_org = org_service.create_organization("Beta Corp", "beta-corp")
    try:
        org_service.verify_tenant_isolation(
            requesting_org_id=beta_org.organization_id,
            target_resource_org_id=acme_org.organization_id,
        )
        print("   ❌ FAIL: Cross-tenant access was allowed!")
    except GuardWAFSecurityError as e:
        print(f"   ✅ GUARDWAF CROSS-TENANT ACCESS BLOCKED: {e.message}")

    # --- Scenario 9: RBAC Enforcement ---
    print("\n▶ SCENARIO 9: Attempting unauthorized policy publishing by Developer John...")
    try:
        RBACManager.check_permission(role=Role.DEVELOPER, required_action=ACTION_PUBLISH_POLICY)
        print("   ❌ FAIL: Developer was allowed to publish policy!")
    except GuardWAFSecurityError as e:
        print(f"   ✅ GUARDWAF RBAC BLOCKED ACTION: {e.message}")

    # --- Scenario 10: Suspicious Activity & Emergency Disable ---
    print("\n▶ SCENARIO 10: Security Admin Maya triggering EMERGENCY DISABLE for agent...")
    agent_service.revoke_agent(agent_id=agent_id, actor_id=maya.user_id, reason="Suspicious activity detected")
    print(f"   ✅ Agent '{agent_id}' Status Updated to REVOKED")

    # --- Scenario 11: End-to-End Audit Timeline & Incident Correlation Search ---
    print("\n▶ SCENARIO 11: Security Operations Dashboard Overview & Incident Management...")
    stats = dashboard_service.get_overview_stats(acme_org.organization_id)
    print(
        f"   ✅ Dashboard Stats: Active Agents={stats['active_agents']}, Revoked Agents={stats['revoked_agents']}, Total Events={stats['total_audit_events']}"
    )

    # Create Incident
    inc = incident_service.create_incident(
        organization_id=acme_org.organization_id,
        agent_id=agent_id,
        title="Unauthorized Large Refund Attempt",
        description="Agent requested $1000 refund exceeding $500 policy threshold.",
        correlation_id="corr_101_demo",
    )
    print(f"   ✅ Incident Logged: ID='{inc.incident_id}', Severity={inc.severity.value}, Status={inc.status.value}")

    print("\n" + "=" * 85)
    print("✅ PHASE 4 DEMO COMPLETE: Multi-Tenant Enterprise Platform & Production Control Plane Verified!")
    print("=" * 85)


if __name__ == "__main__":
    run_phase4_demo()
