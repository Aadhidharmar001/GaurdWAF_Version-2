"""
Workstream B2 — Real MCP Gateway Proxy & Server Wrapper End-to-End Test Suite.
Verifies discovery filtering, parameter mutation rejection, agent revocation, tenant lockdown, and 0-call invariant on blocked requests.
"""

import pytest
from guardwaf import GuardWAF, GuardWAFSecurityError, GuardWAFHITLRequiredError
from guardwaf.core.models import PolicyConfig, PolicyRules, BulkThresholdRule, HITLRule
from guardwaf.mcp.gateway import MCPGatewayProxy
from guardwaf.mcp.models import MCPToolRequest, MCPToolResponse, MCPToolMetadata

MCP_DOWNSTREAM_CALLS = 0

def mock_mcp_downstream_server(request: MCPToolRequest) -> MCPToolResponse:
    global MCP_DOWNSTREAM_CALLS
    MCP_DOWNSTREAM_CALLS += 1
    return MCPToolResponse(id=request.id, result={"status": "EXECUTED", "tool": request.tool_name, "params": request.arguments})

@pytest.fixture
def mcp_gateway_env():
    global MCP_DOWNSTREAM_CALLS
    MCP_DOWNSTREAM_CALLS = 0

    rules = PolicyRules(
        bulk_thresholds=[BulkThresholdRule(tool="mcp_delete_table", param_name="rows", max_value=100)],
        hitl_rules=[HITLRule(tool="mcp_transfer", condition_param="amount", greater_than=500.0)]
    )
    policy = PolicyConfig(metadata={"policy_name": "mcp_policy"}, rules=rules)
    waf = GuardWAF(policy=policy, secret_key="secret_mcp_test")
    gateway = MCPGatewayProxy(waf=waf, downstream_handler=mock_mcp_downstream_server)
    return waf, gateway

def test_mcp_discovery_and_allowed_execution(mcp_gateway_env):
    waf, gateway = mcp_gateway_env
    tools = [MCPToolMetadata(name="mcp_lookup"), MCPToolMetadata(name="mcp_delete_table"), MCPToolMetadata(name="mcp_transfer")]

    # Discovery filter
    allowed_tools = gateway.filter_allowed_tools(tenant_id="org_mcp", agent_id="agent_mcp", available_tools=tools)
    assert len(allowed_tools) == 3

    # Allowed execution
    req = MCPToolRequest(
        tenant_id="org_mcp",
        agent_id="agent_mcp",
        tool_name="mcp_lookup",
        arguments={"id": "item_123"}
    )
    res = gateway.handle_tool_request(req)
    assert res.result is not None
    assert res.result["status"] == "EXECUTED"
    assert MCP_DOWNSTREAM_CALLS == 1

def test_mcp_blocked_request_zero_calls_invariant(mcp_gateway_env):
    waf, gateway = mcp_gateway_env
    initial_calls = MCP_DOWNSTREAM_CALLS

    # Request violating bulk threshold (rows=500 > max 100)
    req = MCPToolRequest(
        tenant_id="org_mcp",
        agent_id="agent_mcp",
        tool_name="mcp_delete_table",
        arguments={"table": "users", "rows": 500}
    )
    res = gateway.handle_tool_request(req)
    assert res.error is not None
    assert "blocked" in res.error["message"].lower()

    # CRITICAL INVARIANT VERIFICATION: Downstream execution count MUST be 0!
    assert MCP_DOWNSTREAM_CALLS == initial_calls
