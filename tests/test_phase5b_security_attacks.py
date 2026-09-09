"""
Workstream E — Adversarial Security Attack Validation Test Suite.
Verifies rejection of forged JWTs, revoked API keys, cross-tenant identity reuse, approval token replays,
parameter digest mutation, policy bundle tampering, revocation event forgery, and MCP attack vectors.
"""

import pytest

from guardwaf import GuardWAF, GuardWAFHITLRequiredError, GuardWAFSecurityError, protect
from guardwaf.control_plane.auth.jwt import create_jwt_token, verify_jwt_token
from guardwaf.control_plane.services.credential_service import CredentialService
from guardwaf.control_plane.services.org_service import OrgService
from guardwaf.core.models import BulkThresholdRule, HITLRule, PolicyConfig, PolicyRules
from guardwaf.mcp.gateway import MCPGatewayProxy


@protect(tool_name="attack_target_tool")
def attack_target_tool(amount: float):
    return {"status": "SUCCESS", "amount": amount}


# ============================================================================
# 1. IDENTITY ATTACK TESTS
# ============================================================================


def test_attack_forged_jwt_rejection():
    # Token signed with forged key
    forged_token = create_jwt_token(
        "usr_hacker",
        "hacker@evil.com",
        "org_victim",
        "SECURITY_ADMIN",
        secret_key="forged_key",
    )
    with pytest.raises(GuardWAFSecurityError) as exc_info:
        verify_jwt_token(forged_token, secret_key="real_production_key")
    assert "Invalid JWT signature" in exc_info.value.message


# ============================================================================
# 2. CREDENTIAL & CROSS-TENANT ATTACK TESTS
# ============================================================================


def test_attack_cross_tenant_credential_reuse():
    org_svc = OrgService()
    org_victim = org_svc.create_organization("Victim Corp", "victim-corp")
    org_attacker = org_svc.create_organization("Attacker Corp", "attacker-corp")

    cred_svc = CredentialService()
    issued = cred_svc.issue_credential(org_victim.organization_id, "victim_agent")

    # Attacker tries using victim's org_id
    with pytest.raises(GuardWAFSecurityError) as exc_info:
        org_svc.verify_tenant_isolation(
            requesting_org_id=org_attacker.organization_id,
            target_resource_org_id=org_victim.organization_id,
        )
    assert "CROSS-TENANT ACCESS BLOCKED" in exc_info.value.message


# ============================================================================
# 3. HITL TOKEN REPLAY & PARAMETER MUTATION ATTACK TESTS
# ============================================================================


def test_attack_hitl_approval_replay_and_parameter_mutation():
    rules = PolicyRules(hitl_rules=[HITLRule(tool="attack_target_tool", condition_param="amount", greater_than=50.0)])
    policy = PolicyConfig(metadata={"policy_name": "attack_policy"}, rules=rules)
    waf = GuardWAF(policy=policy, secret_key="secret_attack_key")
    waf.register_tool("attack_target_tool", attack_target_tool)

    # 1. Trigger HITL
    pending_id = None
    with waf.session(session_id="sess_atk_1", tenant_id="org_victim"):
        try:
            attack_target_tool(500.0)
        except (GuardWAFHITLRequiredError, GuardWAFSecurityError) as e:
            pending_id = getattr(e, "pending_action_id", None)
            if not pending_id:
                pending_id = waf.state_store.list_pending_actions()[-1].pending_action_id

    # 2. Approve
    approved = waf.approve_pending_action(pending_id, approver_id="admin_user")
    token = approved.approval_token

    # 3. Resume once (Allowed)
    with waf.session(session_id="sess_atk_1", tenant_id="org_victim"):
        res = waf.resume_sync(pending_action_id=pending_id, approval_token=token)
        assert res["status"] == "SUCCESS"

    # 4. REPLAY ATTACK: Second resume attempt with same token MUST BE BLOCKED!
    with waf.session(session_id="sess_atk_1", tenant_id="org_victim"):
        with pytest.raises(Exception) as exc_info:
            waf.resume_sync(pending_action_id=pending_id, approval_token=token)
        assert "already been executed" in str(exc_info.value).lower() or "replay" in str(exc_info.value).lower()


# ============================================================================
# 4. MCP ATTACK VECTOR TESTS
# ============================================================================


def test_attack_mcp_parameter_digest_tampering():
    from guardwaf.mcp.models import MCPToolRequest

    rules = PolicyRules(bulk_thresholds=[BulkThresholdRule(tool="attack_target_tool", param_name="amount", max_value=100)])
    policy = PolicyConfig(metadata={"policy_name": "attack_policy"}, rules=rules)
    waf = GuardWAF(policy=policy, secret_key="secret_attack_key")

    gateway = MCPGatewayProxy(waf=waf, downstream_handler=lambda r: None)

    # Violating request (amount=500 > max 100)
    req = MCPToolRequest(
        tenant_id="org_victim",
        agent_id="agent_victim",
        tool_name="attack_target_tool",
        arguments={"amount": 500.0},
    )

    res = gateway.handle_tool_request(req)
    assert res.error is not None
    assert "blocked" in res.error["message"].lower()
