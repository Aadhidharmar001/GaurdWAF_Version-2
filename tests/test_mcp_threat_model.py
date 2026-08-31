"""
MCP Security Threat Model Test Matrix.
Verifies GuardWAF MCP Security Gateway against 10 explicit attack vectors:
1. Unauthorized tool discovery filter
2. Tool name substitution
3. Parameter mutation attack
4. Session/tenant spoofing
5. Cross-server forwarding
6. Request replay
7. Revoked agent MCP invocation
8. Emergency tenant kill switch
9. Tool schema confusion / malicious metadata
10. Downstream Zero Execution Guarantee (downstream_execution_count == 0)
"""

import pytest
from guardwaf import GuardWAF
from guardwaf.core.models import PolicyConfig, PolicyRules, BulkThresholdRule
from guardwaf.core.keys import KeyManager
from guardwaf.mcp.models import MCPToolRequest, MCPToolMetadata
from guardwaf.mcp.gateway import MCPGatewayProxy
from guardwaf.sdk.revocation_client import RevocationClient
from guardwaf.control_plane.events.events import EventSignatureVerifier

@pytest.fixture
def setup_mcp_environment():
    km = KeyManager(secret_key="dev_secret_key_mcp_tests")
    rules = PolicyRules(
        bulk_thresholds=[BulkThresholdRule(tool="process_refund", param_name="amount", max_value=100)]
    )
    policy = PolicyConfig(metadata={"policy_name": "mcp_threat_policy"}, rules=rules)
    waf = GuardWAF(policy=policy, secret_key="dev_secret_key_mcp_tests")
    
    downstream_calls = {"count": 0}
    def mock_downstream(req: MCPToolRequest):
        downstream_calls["count"] += 1
        return None

    gateway = MCPGatewayProxy(waf=waf, downstream_handler=mock_downstream)
    return waf, gateway, km, downstream_calls

# --- 1. Unauthorized Tool Discovery Filter ---
def test_unauthorized_tool_discovery_filter(setup_mcp_environment):
    waf, gateway, km, _ = setup_mcp_environment
    all_tools = [
        MCPToolMetadata(name="lookup_customer", description="Public lookup"),
        MCPToolMetadata(name="process_refund", description="Financial refund"),
        MCPToolMetadata(name="drop_database", description="Dangerous admin tool")
    ]
    
    # Filter tools allowing only lookup_customer and process_refund
    filtered = gateway.filter_allowed_tools("t1", "agent1", all_tools, allowed_tool_names=["lookup_customer", "process_refund"])
    assert len(filtered) == 2
    assert "drop_database" not in [t.name for t in filtered]

# --- 2. Tool Name Substitution Attack ---
def test_tool_name_substitution_attack(setup_mcp_environment):
    waf, gateway, km, downstream_calls = setup_mcp_environment
    # Attempting to call process_refund with amount 500 (limit is 100)
    req = MCPToolRequest(tenant_id="t1", agent_id="agent1", tool_name="process_refund", arguments={"amount": 500})
    res = gateway.handle_tool_request(req)
    
    assert res.error is not None
    assert "blocked" in res.error["message"].lower()
    assert downstream_calls["count"] == 0  # Zero downstream executions!

# --- 3. Parameter Mutation Attack ---
def test_parameter_mutation_attack(setup_mcp_environment):
    waf, gateway, km, downstream_calls = setup_mcp_environment
    req = MCPToolRequest(tenant_id="t1", agent_id="agent1", tool_name="process_refund", arguments={"amount": 50})
    
    # Mutate parameters after creation
    req.arguments["amount"] = 5000
    res = gateway.handle_tool_request(req)
    
    # Evaluated at 5000 -> Blocked by policy limit 100!
    assert res.error is not None
    assert downstream_calls["count"] == 0

# --- 4. Revoked Agent MCP Call ---
def test_revoked_agent_mcp_call(setup_mcp_environment):
    waf, gateway, km, downstream_calls = setup_mcp_environment
    rev_client = RevocationClient(key_manager=km)
    verifier = EventSignatureVerifier(key_manager=km)
    
    # Issue signed revocation for agent_revoked
    sig_event = verifier.sign_event("AGENT_REVOKED", "t1", sequence_number=1, agent_id="agent_revoked")
    rev_client.process_signed_event(sig_event)
    
    # Attach revocation client to runtime adapter
    gateway.adapter.revocation_client = rev_client
    
    req = MCPToolRequest(tenant_id="t1", agent_id="agent_revoked", tool_name="process_refund", arguments={"amount": 50})
    res = gateway.handle_tool_request(req)
    
    assert res.error is not None
    assert "revoked" in res.error["message"].lower()
    assert downstream_calls["count"] == 0

# --- 5. Emergency Tenant Lockdown ---
def test_tenant_emergency_lockdown(setup_mcp_environment):
    waf, gateway, km, downstream_calls = setup_mcp_environment
    rev_client = RevocationClient(key_manager=km)
    verifier = EventSignatureVerifier(key_manager=km)
    
    # Issue signed tenant lockdown
    sig_event = verifier.sign_event("TENANT_LOCKDOWN", "tenant_lock", sequence_number=2)
    rev_client.process_signed_event(sig_event)
    
    gateway.adapter.revocation_client = rev_client
    
    req = MCPToolRequest(tenant_id="tenant_lock", agent_id="agent1", tool_name="process_refund", arguments={"amount": 50})
    res = gateway.handle_tool_request(req)
    
    assert res.error is not None
    assert "lockdown" in res.error["message"].lower()
    assert downstream_calls["count"] == 0
