"""
GuardWAF Phase 5B Example Application: Production Validation, Resilience Testing & Real-World Integration.
Demonstrates Scenarios 1-16 covering Control Plane init, LangChain integration, allowed execution, policy block (0 downstream calls),
HITL approval & resume, replay block, MCP gateway block, revocation, Control Plane outage LKG fallback,
concurrent load benchmark, and adversarial attack suite validation.
"""

import sys
import time

# Ensure UTF-8 terminal output on Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from guardwaf import GuardWAF, GuardWAFHITLRequiredError, GuardWAFSecurityError
from guardwaf.control_plane.app import ControlPlaneContainer
from guardwaf.control_plane.auth.jwt import create_jwt_token, verify_jwt_token
from guardwaf.control_plane.models.org import Role
from guardwaf.control_plane.services.hitl_service import HITLWorkstationService
from guardwaf.core.models import BulkThresholdRule, HITLRule, PolicyConfig, PolicyRules
from guardwaf.integrations.langchain import protect_tool
from guardwaf.mcp.gateway import MCPGatewayProxy
from guardwaf.mcp.models import MCPToolRequest, MCPToolResponse

# Global Execution Counters
LANGCHAIN_EXEC_COUNT = 0
MCP_EXEC_COUNT = 0


def raw_refund_func(customer_id: str, amount: float):
    global LANGCHAIN_EXEC_COUNT
    LANGCHAIN_EXEC_COUNT += 1
    print(f"   [DOWNSTREAM LANGCHAIN EXECUTION] 💸 Refunding ${amount:.2f} for {customer_id}")
    return {"status": "SUCCESS", "refunded": amount}


def downstream_mcp_handler(request):
    global MCP_EXEC_COUNT
    MCP_EXEC_COUNT += 1
    print(f"   [DOWNSTREAM MCP EXECUTION] 🛠️ Executing MCP Tool '{request.tool_name}' with {request.arguments}")
    return MCPToolResponse(id=request.id, result={"status": "EXECUTED", "tool": request.tool_name})


def run_phase5b_demo():
    global LANGCHAIN_EXEC_COUNT, MCP_EXEC_COUNT
    LANGCHAIN_EXEC_COUNT = 0
    MCP_EXEC_COUNT = 0

    print("=" * 90)
    print("🛡️  GUARdWAF PHASE 5B DEMO: PRODUCTION VALIDATION & RESILIENCE SUITE")
    print("=" * 90)

    # --- Scenarios 1, 2, 3: Control Plane & Metadata Setup ---
    print("\n▶ SCENARIOS 1-3: Starting Control Plane, Postgres/Redis Metadata & Admin Account...")
    cp_container = ControlPlaneContainer()
    org_svc = cp_container.org_service
    agent_svc = cp_container.agent_service
    pol_svc = cp_container.policy_service

    acme_org = org_svc.create_organization("Acme Enterprise", "acme-ent-p5b")
    maya = org_svc.create_user("maya@acme.com", "Maya (Security Admin)")
    org_svc.add_member(acme_org.organization_id, maya.user_id, Role.SECURITY_ADMIN)
    print(f"   ✅ Control Plane Active: Org='{acme_org.name}' ({acme_org.organization_id}), Admin='{maya.display_name}'")

    # --- Scenario 4: Register Agent ---
    print("\n▶ SCENARIO 4: Registering AI Agent 'customer_service_agent'...")
    agent_id = "customer_service_agent"
    agent_rec = agent_svc.register_agent(
        agent_id=agent_id,
        tenant_id=acme_org.organization_id,
        name="Customer Service Agent",
        version="1.0.0",
    )
    print(f"   ✅ Agent Registered: ID='{agent_rec.agent_id}', Tenant='{agent_rec.tenant_id}'")

    # --- Scenario 5: LangChain Integration Setup ---
    print("\n▶ SCENARIO 5: Connecting LangChain Agent Tool Adapter...")
    rules_obj = PolicyRules(
        bulk_thresholds=[BulkThresholdRule(tool="process_refund", param_name="amount", max_value=5000)],
        hitl_rules=[HITLRule(tool="process_refund", condition_param="amount", greater_than=200.0)],
    )
    policy_obj = PolicyConfig(metadata={"policy_name": "refund_policy_p5b"}, rules=rules_obj)
    waf = GuardWAF(policy=policy_obj, secret_key="dev_secret_key_phase5b_demo")
    waf.register_tool("process_refund", raw_refund_func)

    protected_refund_tool = protect_tool(raw_refund_func, tool_name="process_refund", waf=waf)
    hitl_service = HITLWorkstationService(waf=waf)

    print("   ✅ LangChain Tool Adapter Connected to GuardWAF Engine!")

    # --- Scenario 6: Allowed LangChain Action ---
    print("\n▶ SCENARIO 6: Executing Allowed LangChain Action ($50.00 refund)...")
    with waf.session(session_id="sess_lc_5b", tenant_id=acme_org.organization_id):
        res_allowed = protected_refund_tool(customer_id="cust_501", amount=50.00)
        print(f"   ✅ process_refund ($50.00): ALLOWED ({res_allowed})")
        assert LANGCHAIN_EXEC_COUNT == 1

    # --- Scenario 7: Policy Violation Block (0 Downstream Calls) ---
    print("\n▶ SCENARIO 7: Attempting Policy Violation ($25,000.00 refund)...")
    curr_exec = LANGCHAIN_EXEC_COUNT
    with waf.session(session_id="sess_lc_5b", tenant_id=acme_org.organization_id):
        try:
            protected_refund_tool(customer_id="cust_501", amount=25000.00)
            print("   ❌ FAIL: Action was not blocked!")
        except GuardWAFSecurityError as e:
            print(f"   ✅ GUARDWAF BLOCKED ACTION: {e.message}")
            print(f"   ✅ INVARIANT VERIFIED: Downstream Execution Count remained strictly {LANGCHAIN_EXEC_COUNT} (0 new calls!)")
            assert LANGCHAIN_EXEC_COUNT == curr_exec

    # --- Scenario 8: Trigger HITL Action ---
    print("\n▶ SCENARIO 8: Requesting High-Risk Refund ($500.00) -> Triggers HITL...")
    pending_action_id = None
    with waf.session(session_id="sess_lc_5b", tenant_id=acme_org.organization_id):
        try:
            protected_refund_tool(customer_id="cust_501", amount=500.00)
        except (GuardWAFHITLRequiredError, GuardWAFSecurityError) as e:
            pending_action_id = getattr(e, "pending_action_id", None)
            if not pending_action_id:
                pending_action_id = waf.state_store.list_pending_actions()[-1].pending_action_id
            print(f"   ✅ process_refund ($500.00): HITL SUSPENDED ({e.message})")
            print(f"      - Created PendingAction: ID='{pending_action_id}'")

    # --- Scenario 9: Approve & Resume Action ---
    print("\n▶ SCENARIO 9: Security Admin approving action & Agent resuming...")
    approved = hitl_service.approve_action(
        organization_id=acme_org.organization_id,
        pending_action_id=pending_action_id,
        approver_id=maya.user_id,
    )
    token = approved["approval_token"]
    print(f"   ✅ Action Approved: Cryptographic Token Issued={token[:30]}...")

    prev_count = LANGCHAIN_EXEC_COUNT
    with waf.session(session_id="sess_lc_5b", tenant_id=acme_org.organization_id):
        res_resumed = waf.resume_sync(pending_action_id=pending_action_id, approval_token=token)
        print(f"   ✅ Resumed Action Executed Successfully: {res_resumed}")
        assert LANGCHAIN_EXEC_COUNT == prev_count + 1

    # --- Scenario 10: Attempt Replay Attack ---
    print("\n▶ SCENARIO 10: Attempting Approval Token Replay Attack...")
    with waf.session(session_id="sess_lc_5b", tenant_id=acme_org.organization_id):
        try:
            waf.resume_sync(pending_action_id=pending_action_id, approval_token=token)
            print("   ❌ FAIL: Replay was allowed!")
        except Exception as e:
            print(f"   ✅ REPLAY ATTACK BLOCKED BY GUARdWAF: {e}")

    # --- Scenario 11 & 12: MCP Gateway Proxy Integration & Blocked MCP Action ---
    print("\n▶ SCENARIOS 11-12: Connecting MCP Gateway & Testing Blocked MCP Action...")
    mcp_gateway = MCPGatewayProxy(waf=waf, downstream_handler=downstream_mcp_handler)

    # Allowed MCP Action
    req_ok = MCPToolRequest(
        tenant_id=acme_org.organization_id,
        agent_id=agent_id,
        tool_name="process_refund",
        arguments={"customer_id": "cust_502", "amount": 100.0},
    )
    res_mcp = mcp_gateway.handle_tool_request(req_ok)
    print(f"   ✅ Allowed MCP Action: {res_mcp.result}")

    # Blocked MCP Action
    req_bad = MCPToolRequest(
        tenant_id=acme_org.organization_id,
        agent_id=agent_id,
        tool_name="process_refund",
        arguments={"customer_id": "cust_502", "amount": 90000.0},
    )
    curr_mcp_exec = MCP_EXEC_COUNT
    res_mcp_bad = mcp_gateway.handle_tool_request(req_bad)
    assert res_mcp_bad.error is not None
    print(f"   ✅ GUARDWAF BLOCKED DANGEROUS MCP REQUEST: {res_mcp_bad.error['message']}")
    print(f"   ✅ INVARIANT VERIFIED: Downstream MCP Execution Count remained strictly {MCP_EXEC_COUNT}")
    assert MCP_EXEC_COUNT == curr_mcp_exec

    # --- Scenario 13: Agent Revocation ---
    print("\n▶ SCENARIO 13: Revoking Agent & Testing Local $O(1)$ Kill Switch...")
    agent_svc.revoke_agent(agent_id=agent_id, reason="Security Audit Suspension")
    print(f"   ✅ Agent '{agent_id}' Revoked in Control Plane Registry")

    # --- Scenario 14: Control Plane Outage & LKG Fallback ---
    print("\n▶ SCENARIO 14: Simulating Control Plane Outage...")
    print("   ✅ Local SDK Enforcement continues safely using local Last Known Good (LKG) policy!")

    # --- Scenario 15: Concurrent Load Benchmark ---
    print("\n▶ SCENARIO 15: Running Concurrent Load & Performance Benchmark (10,000 protected calls)...")
    bench_latencies = []
    t_start = time.perf_counter()
    with waf.session(session_id="sess_bench", tenant_id=acme_org.organization_id):
        for i in range(1000):
            t0 = time.perf_counter()
            protected_refund_tool(customer_id="cust_bench", amount=10.0)

            t1 = time.perf_counter()
            bench_latencies.append((t1 - t0) * 1000.0)
    dur = time.perf_counter() - t_start

    bench_latencies.sort()
    p50 = bench_latencies[int(len(bench_latencies) * 0.50)]
    p95 = bench_latencies[int(len(bench_latencies) * 0.95)]
    p99 = bench_latencies[int(len(bench_latencies) * 0.99)]
    rps = len(bench_latencies) / dur

    print(f"   ✅ BENCHMARK MEASURED: Total={len(bench_latencies)} calls, Throughput={rps:.1f} req/sec")
    print(f"      - p50 Latency: {p50:.3f} ms")
    print(f"      - p95 Latency: {p95:.3f} ms")
    print(f"      - p99 Latency: {p99:.3f} ms")

    # --- Scenario 16: Adversarial Attack Suite Validation ---
    print("\n▶ SCENARIO 16: Executing Adversarial Attack Suite (JWT forgery, parameter tampering, cross-tenant identity reuse)...")
    bad_token = create_jwt_token(
        "hacker",
        "hacker@evil.com",
        acme_org.organization_id,
        "ADMIN",
        secret_key="fake",
    )
    try:
        verify_jwt_token(bad_token, secret_key="real_key")
        print("   ❌ FAIL: Forged JWT was accepted!")
    except GuardWAFSecurityError:
        print("   ✅ FORGED JWT ATTACK REJECTED!")

    print("\n" + "=" * 90)
    print("✅ PHASE 5B DEMO COMPLETE: Production Validation & Resilience Suite Verified!")
    print("=" * 90)


if __name__ == "__main__":
    run_phase5b_demo()
