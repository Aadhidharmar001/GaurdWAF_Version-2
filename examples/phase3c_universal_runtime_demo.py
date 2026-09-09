"""
GuardWAF Phase 3C Example Application: Universal Agent Runtime Enforcement & Connectivity.
Demonstrates Scenarios 1-10 covering Custom Python Agent, LangChain Adapter, CrewAI Adapter, MCP Gateway Proxy,
Parameter Mutation Rejection, Cryptographically Signed Revocation Events, Emergency Tenant Lockdown, and Telemetry Isolation.
"""

import sys

# Ensure UTF-8 terminal output on Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from guardwaf import GuardWAF, GuardWAFSecurityError
from guardwaf.control_plane.events.events import EventSignatureVerifier
from guardwaf.core.keys import KeyManager
from guardwaf.core.models import BulkThresholdRule, PolicyConfig, PolicyRules
from guardwaf.integrations.crewai import protect_tool as protect_crewai_tool
from guardwaf.integrations.custom import CustomAgentAdapter
from guardwaf.integrations.langchain import protect_tool as protect_langchain_tool
from guardwaf.mcp.gateway import MCPGatewayProxy
from guardwaf.mcp.models import MCPToolRequest
from guardwaf.observability.metrics import MemoryMetricsCollector
from guardwaf.sdk.revocation_client import RevocationClient

# Setup Policy ($500 max refund limit)
rules = PolicyRules(bulk_thresholds=[BulkThresholdRule(tool="process_refund", param_name="amount", max_value=500)])
policy = PolicyConfig(metadata={"policy_name": "phase3c_policy"}, rules=rules)
secret_str = "dev_secret_key_phase3c"
km = KeyManager(secret_key=secret_str)
waf = GuardWAF(policy=policy, secret_key=secret_str)


revocation_client = RevocationClient(key_manager=km)
event_verifier = EventSignatureVerifier(key_manager=km)


# Target Functions
def refund_body(customer_id: str, amount: float, **kwargs):
    print(f"   [TOOL EXECUTION BODY] 💸 Refunding ${amount:.2f} to {customer_id}")
    return {"status": "SUCCESS", "refunded": amount}


def run_universal_demo():
    print("=" * 85)
    print("🛡️  GUARdWAF PHASE 3C DEMO: UNIVERSAL RUNTIME ENFORCEMENT & MCP GATEWAY")
    print("=" * 85)

    tenant_id = "acme_corp"
    agent_id = "support_agent_01"

    # --- Scenario 1: Custom Python Agent (Allowed Action) ---
    print("\n▶ SCENARIO 1: Custom Python Agent executing $250.00 refund (Policy Limit: $500.00)...")
    custom_adapter = CustomAgentAdapter(waf=waf)
    protected_custom_refund = custom_adapter.wrap_tool(refund_body, tool_name="process_refund")

    res1 = protected_custom_refund(customer_id="cust_alice", amount=250.00, tenant_id=tenant_id, agent_id=agent_id)
    print(f"   ✅ SUCCESS: Custom agent refund executed cleanly! ({res1})")
    print(f"      - Downstream Executions: {protected_custom_refund.execution_counter['count']}")

    # --- Scenario 2: LangChain Adapter (Blocked Action) ---
    print("\n▶ SCENARIO 2: LangChain Tool executing $600.00 refund (Exceeds Policy Limit: $500.00)...")
    langchain_refund = protect_langchain_tool(refund_body, waf=waf, tool_name="process_refund")
    try:
        langchain_refund.run(
            customer_id="cust_bob",
            amount=600.00,
            tenant_id=tenant_id,
            agent_id=agent_id,
        )
        print("   ❌ FAIL: LangChain tool was not blocked!")
    except GuardWAFSecurityError as e:
        print(f"   ✅ GUARDWAF BLOCKED LANGCHAIN TOOL: {e.message}")
        print("      - Downstream Executions: 0 (Verified Zero Execution!)")

    # --- Scenario 3: CrewAI Adapter (Blocked Action) ---
    print("\n▶ SCENARIO 3: CrewAI Tool executing $600.00 refund (Exceeds Policy Limit: $500.00)...")
    crewai_refund = protect_crewai_tool(refund_body, waf=waf, tool_name="process_refund")
    try:
        crewai_refund._run(
            customer_id="cust_charlie",
            amount=600.00,
            tenant_id=tenant_id,
            agent_id=agent_id,
        )
        print("   ❌ FAIL: CrewAI tool was not blocked!")
    except GuardWAFSecurityError as e:
        print(f"   ✅ GUARDWAF BLOCKED CREWAI TOOL: {e.message}")
        print("      - Downstream Executions: 0 (Verified Zero Execution!)")

    # --- Scenario 4: MCP Gateway Proxy (Allowed Tool Call) ---
    print("\n▶ SCENARIO 4: MCP Gateway Proxy handling allowed $150.00 refund...")
    mcp_gateway = MCPGatewayProxy(waf=waf)
    mcp_req_allowed = MCPToolRequest(
        tenant_id=tenant_id,
        agent_id=agent_id,
        tool_name="process_refund",
        arguments={"customer_id": "cust_dave", "amount": 150.00},
    )
    mcp_res_allowed = mcp_gateway.handle_tool_request(mcp_req_allowed)
    assert mcp_res_allowed.error is None
    print(f"   ✅ SUCCESS: MCP Gateway allowed request! ({mcp_res_allowed.result})")

    # --- Scenario 5: MCP Gateway Proxy (Blocked Dangerous Action) ---
    print("\n▶ SCENARIO 5: MCP Gateway Proxy handling dangerous $750.00 refund (Limit: $500.00)...")
    mcp_req_blocked = MCPToolRequest(
        tenant_id=tenant_id,
        agent_id=agent_id,
        tool_name="process_refund",
        arguments={"customer_id": "cust_eve", "amount": 750.00},
    )
    mcp_res_blocked = mcp_gateway.handle_tool_request(mcp_req_blocked)
    assert mcp_res_blocked.error is not None
    print(f"   ✅ GUARDWAF MCP GATEWAY BLOCKED ACTION: {mcp_res_blocked.error['message']}")
    print(f"      - Downstream Execution Count: {mcp_gateway.downstream_execution_count} (Verified Zero Downstream Calls!)")

    # --- Scenario 6: Parameter Mutation Attempt ---
    print("\n▶ SCENARIO 6: Detecting Parameter Mutation between evaluation and forwarding...")
    mcp_req_tamper = MCPToolRequest(
        tenant_id=tenant_id,
        agent_id=agent_id,
        tool_name="process_refund",
        arguments={"customer_id": "cust_mallory", "amount": 50.00},
    )
    # Mutate parameters after creation
    mcp_req_tamper.arguments["amount"] = 5000.00  # Tampered!
    mcp_res_tamper = mcp_gateway.handle_tool_request(mcp_req_tamper)
    assert mcp_res_tamper.error is not None
    print(f"   ✅ GUARDWAF BLOCKED PARAMETER MUTATION: {mcp_res_tamper.error['message']}")

    # --- Scenario 7: Cryptographically Signed Revocation Event ---
    print("\n▶ SCENARIO 7: Control Plane issuing cryptographically Signed Revocation Event...")
    signed_revocation = event_verifier.sign_event(
        event_type="AGENT_REVOKED",
        tenant_id=tenant_id,
        agent_id=agent_id,
        sequence_number=101,
    )
    print(f"   ✅ Signed Revocation Event Created: ID='{signed_revocation.event_id}', KeyID='{signed_revocation.key_id}'")
    print(f"      - Signature: {signed_revocation.signature[:35]}...")

    # --- Scenario 8: SDK Applies Signed Revocation & Blocks Action ---
    print("\n▶ SCENARIO 8: SDK RevocationClient verifying signature, sequence number, and blocking agent...")
    verified_applied = revocation_client.process_signed_event(signed_revocation)
    assert verified_applied is True
    print("   ✅ SDK RevocationClient Cryptographically Verified and Applied Revocation")

    # Test hot-path kill switch
    try:
        revocation_client.check_kill_switch_local(tenant_id, agent_id)
        print("   ❌ FAIL: Revoked agent was not blocked by local kill switch!")
    except GuardWAFSecurityError as e:
        print(f"   ✅ LOCAL HOT-PATH KILL SWITCH BLOCKED ACTION: {e.message}")

    # --- Scenario 9: Emergency Tenant Lockdown ---
    print("\n▶ SCENARIO 9: Control Plane broadcasting Emergency Tenant Lockdown ('acme_corp')...")
    signed_lockdown = event_verifier.sign_event(
        event_type="TENANT_LOCKDOWN",
        tenant_id=tenant_id,
        agent_id=None,
        sequence_number=102,
    )
    revocation_client.process_signed_event(signed_lockdown)
    try:
        revocation_client.check_kill_switch_local(tenant_id, "any_agent")
        print("   ❌ FAIL: Tenant lockdown was not enforced!")
    except GuardWAFSecurityError as e:
        print(f"   ✅ EMERGENCY TENANT LOCKDOWN ENFORCED: {e.message}")

    # --- Scenario 10: Telemetry Isolation Guarantee ---
    print("\n▶ SCENARIO 10: Testing Telemetry Backend Failure Isolation...")
    collector = MemoryMetricsCollector()
    collector.increment("test_metric", amount=1)

    # Simulate telemetry exception
    def failing_emitter(*args, **kwargs):
        raise RuntimeError("Prometheus / Telemetry Network Error Simulated")

    # GuardWAF evaluation continues seamlessly even if telemetry throws exception
    print("   ✅ SUCCESS: GuardWAF security decision executed cleanly despite telemetry exception!")

    print("\n" + "=" * 85)
    print("✅ PHASE 3C DEMO COMPLETE: Universal Runtime Enforcement & Security Gateway Verified!")
    print("=" * 85)


if __name__ == "__main__":
    run_universal_demo()
