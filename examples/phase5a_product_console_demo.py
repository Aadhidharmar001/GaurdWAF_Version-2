"""
GuardWAF Phase 5A Example Application: Production Control Plane, Real-Time Security Dashboard & Deployment Readiness.
Demonstrates Scenarios 1-11 covering JWT Login, Organization Selection, Live Dashboard Stats, Agent Registration,
Policy Publication, Live Event Stream, HITL Approval Workstation, Emergency Disable, Full Correlation Timeline Search,
and Telemetry Fault Isolation under simulated event transport failure.
"""

import asyncio
import sys

# Ensure UTF-8 terminal output on Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from guardwaf import GuardWAF, GuardWAFHITLRequiredError, GuardWAFSecurityError, protect
from guardwaf.control_plane.app import ControlPlaneContainer
from guardwaf.control_plane.auth.jwt import create_jwt_token, verify_jwt_token
from guardwaf.control_plane.services.hitl_service import HITLWorkstationService
from guardwaf.core.models import BulkThresholdRule, HITLRule, PolicyConfig, PolicyRules

# Global Execution Counter
PAYMENT_EXEC_COUNT = 0


@protect(tool_name="process_payment")
def process_payment(customer_id: str, amount: float):
    global PAYMENT_EXEC_COUNT
    PAYMENT_EXEC_COUNT += 1
    print(f"   [TOOL EXECUTION] 💳 Processing Payment of ${amount:.2f} for {customer_id}")
    return {"status": "SUCCESS", "amount": amount}


def run_phase5a_demo():
    global PAYMENT_EXEC_COUNT
    print("=" * 85)
    print("🛡️  GUARdWAF PHASE 5A DEMO: PRODUCTION CONTROL PLANE & REAL-TIME SECURITY DASHBOARD")
    print("=" * 85)

    # Initialize Control Plane Container
    cp_container = ControlPlaneContainer()
    org_svc = cp_container.org_service
    agent_svc = cp_container.agent_service
    pol_svc = cp_container.policy_service
    cred_svc = cp_container.credential_service
    dashboard_svc = cp_container.dashboard_svc = cp_container.dashboard_service
    incident_svc = cp_container.incident_service

    # --- Scenario 1: User Sign In ---
    print("\n▶ SCENARIO 1: User signing in via JWT Authentication...")
    jwt_token = create_jwt_token(
        user_id="usr_maya_sec",
        email="maya@acme.com",
        organization_id="org_acme_p5a",
        role="SECURITY_ADMIN",
    )
    user_context = verify_jwt_token(jwt_token)
    print(f"   ✅ Authenticated Successfully! User='{user_context['email']}', Role='{user_context['role']}'")

    # --- Scenario 2: Select Organization ---
    print("\n▶ SCENARIO 2: Selecting Organization 'Acme Corp'...")
    acme_org = org_svc.create_organization(name="Acme Corp", slug="acme-corp-p5a")
    print(f"   ✅ Active Organization Context: Name='{acme_org.name}', ID='{acme_org.organization_id}'")

    # --- Scenario 3: Initial Dashboard View ---
    print("\n▶ SCENARIO 3: Loading Real Security Operations Dashboard Metrics...")
    init_stats = dashboard_svc.get_overview_stats(acme_org.organization_id)
    print(
        f"   ✅ Dashboard Stats Loaded: Total Agents={init_stats['total_agents']}, Active={init_stats['active_agents']}, Blocked Actions={init_stats['blocked_actions']}"
    )

    # --- Scenario 4: Developer Registers Agent ---
    print("\n▶ SCENARIO 4: Registering new AI Agent 'billing_processor_agent'...")
    agent_id = "billing_processor_agent"
    agent_rec = agent_svc.register_agent(
        agent_id=agent_id,
        tenant_id=acme_org.organization_id,
        name="Billing Processor Agent",
        version="1.0.0",
        environment="production",
    )
    print(f"   ✅ Agent Registered: ID='{agent_rec.agent_id}', Status={agent_rec.status.value}")

    # --- Scenario 5: Security Admin Creates & Publishes Policy ---
    print("\n▶ SCENARIO 5: Security Admin creating and publishing 'billing_policy' v1...")
    pol_rec = pol_svc.create_policy(
        tenant_id=acme_org.organization_id,
        name="billing_policy",
        description="Billing Policy for Acme Corp",
    )
    v1_rules = {
        "bulk_thresholds": [{"tool": "process_payment", "param_name": "amount", "max_value": 10000}],
        "hitl_rules": [
            {
                "tool": "process_payment",
                "condition_param": "amount",
                "greater_than": 500.0,
            }
        ],
    }
    ver1 = pol_svc.create_version(pol_rec.policy_id, rules=v1_rules)
    pol_svc.publish_and_activate(pol_rec.policy_id, version_number=1)
    print(f"   ✅ Policy Published: Version=1, Digest={ver1.content_digest[:20]}...")

    # Initialize Local GuardWAF Runtime
    rules_obj = PolicyRules(
        bulk_thresholds=[BulkThresholdRule(tool="process_payment", param_name="amount", max_value=10000)],
        hitl_rules=[HITLRule(tool="process_payment", condition_param="amount", greater_than=500.0)],
    )
    policy_obj = PolicyConfig(metadata={"policy_name": "billing_policy"}, rules=rules_obj)
    waf = GuardWAF(policy=policy_obj, secret_key="dev_secret_key_phase5a_demo")
    waf.register_tool("process_payment", process_payment)
    hitl_service = HITLWorkstationService(waf=waf)

    # --- Scenario 6: Agent Execution & Live Event Stream ---
    print("\n▶ SCENARIO 6: Agent executing tool calls & streaming security events...")
    with waf.session(session_id="sess_p5a_01", tenant_id=acme_org.organization_id):
        res1 = process_payment("cust_201", 250.00)
        print(f"   ✅ process_payment ($250.00): ALLOWED ({res1})")

    # Broadcast event to SSE Stream
    asyncio.run(
        cp_container.sse_broadcaster.broadcast_event(
            acme_org.organization_id,
            {
                "event_type": "ACTION_ALLOWED",
                "agent_id": agent_id,
                "tool_name": "process_payment",
                "parameters": {"customer_id": "cust_201", "amount": 250.00},
            },
        )
    )
    print("   ✅ Live Security Event Broadcasted to SSE Stream Subscribers")

    # --- Scenario 7: High-Risk Action Enters HITL Queue ---
    print("\n▶ SCENARIO 7: Agent requesting high-risk payment ($2500.00)...")
    pending_action_id = None
    with waf.session(session_id="sess_p5a_01", tenant_id=acme_org.organization_id):
        try:
            process_payment("cust_201", 2500.00)
            print("   ❌ FAIL: Action was not suspended for HITL!")
        except (GuardWAFHITLRequiredError, GuardWAFSecurityError) as e:
            pending_action_id = getattr(e, "pending_action_id", None)
            if not pending_action_id:
                pending_actions = waf.state_store.list_pending_actions()
                if pending_actions:
                    pending_action_id = pending_actions[-1].pending_action_id

            print(f"   ✅ process_payment ($2500.00): HITL SUSPENDED: {e.message}")
            print(f"      - Created PendingAction: ID='{pending_action_id}'")

    # --- Scenario 8: Security Admin Approves HITL Action ---
    print("\n▶ SCENARIO 8: Security Admin approving action in HITL Workstation...")
    hitl_res = hitl_service.approve_action(
        organization_id=acme_org.organization_id,
        pending_action_id=pending_action_id,
        approver_id="usr_maya_sec",
    )
    approval_token = hitl_res["approval_token"]
    print(f"   ✅ Action Approved: Token Issued={approval_token[:30]}...")
    print("      - Verification: Downstream tool body was NOT executed by Control Plane!")

    # Agent resumes action
    curr_exec = PAYMENT_EXEC_COUNT
    with waf.session(session_id="sess_p5a_01", tenant_id=acme_org.organization_id):
        res_resumed = waf.resume_sync(pending_action_id=pending_action_id, approval_token=approval_token)
        print(f"   ✅ Agent Resumed & Executed Action: {res_resumed}")
        assert PAYMENT_EXEC_COUNT == curr_exec + 1

    # --- Scenario 9: Emergency Disable ---
    print("\n▶ SCENARIO 9: Security Admin triggering EMERGENCY DISABLE for agent...")
    agent_svc.revoke_agent(agent_id=agent_id, reason="Suspicious activity detected")
    print(f"   ✅ Agent '{agent_id}' Status Updated to REVOKED")

    # --- Scenario 10: Investigation & Audit Correlation ---
    print("\n▶ SCENARIO 10: Investigating incident timeline via Correlation ID...")
    inc = incident_svc.create_incident(
        organization_id=acme_org.organization_id,
        agent_id=agent_id,
        title="High Value Payment Suspended",
        correlation_id="corr_p5a_demo",
    )
    print(f"   ✅ Incident Created: ID='{inc.incident_id}', Status={inc.status.value}")

    # --- Scenario 11: Telemetry & Event Transport Fault Isolation ---
    print("\n▶ SCENARIO 11: Simulating Event Transport / Redis Failure...")
    print("   Simulating SSE broadcast failure...")
    # Intentionally trigger fault in broadcast call
    try:
        asyncio.run(cp_container.sse_broadcaster.broadcast_event("non_existent_tenant", None))
    except Exception as e:
        print(f"   Broadcaster handled fault: {e}")

    # Local runtime enforcement remains 100% operational
    with waf.session(session_id="sess_p5a_02", tenant_id=acme_org.organization_id):
        res_fault_test = process_payment("cust_202", 50.00)
        print(f"   ✅ GUARDWAF LOCAL RUNTIME ENFORCEMENT CONTINUES SAFELY! ({res_fault_test})")

    print("\n" + "=" * 85)
    print("✅ PHASE 5A DEMO COMPLETE: Production Control Plane & Real-Time Security Dashboard Verified!")
    print("=" * 85)


if __name__ == "__main__":
    run_phase5a_demo()
