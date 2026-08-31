"""
Comprehensive Phase 3B Unit Test Suite for GuardWAF Enterprise Control Plane,
Signed Policy Distribution, Policy Versioning/Rollback, and SDK PolicyClient.
"""

import time
import pytest
from datetime import datetime, timedelta, timezone
from fastapi.testclient import TestClient

from guardwaf import GuardWAF, protect, VerifiedPrincipal, AgentIdentity, GuardWAFSecurityError
from guardwaf.control_plane.models.agent import AgentStatus
from guardwaf.control_plane.models.policy import PolicyStatus
from guardwaf.control_plane.models.bundle import SignedPolicyBundle
from guardwaf.control_plane.models.authority import AuthorityStatus
from guardwaf.control_plane.app import create_control_plane_app, ControlPlaneContainer
from guardwaf.control_plane.services.agent_service import AgentService
from guardwaf.control_plane.services.policy_service import PolicyService
from guardwaf.control_plane.services.bundle_service import BundleService
from guardwaf.control_plane.services.authority_service import AuthorityService
from guardwaf.sdk.policy_client import PolicyClient, PolicyClientMode
from guardwaf.core.keys import KeyManager
from guardwaf.exceptions import GuardWAFSecurityError, GuardWAFConfigurationError

@pytest.fixture
def cp_container():
    return ControlPlaneContainer()

@pytest.fixture
def api_client(cp_container):
    app = create_control_plane_app(container=cp_container)
    return TestClient(app)

# ============================================================================
# 1. AGENT REGISTRY & REVOCATION TESTS
# ============================================================================

def test_agent_registration_and_lookup(cp_container):
    svc: AgentService = cp_container.agent_service
    agent = svc.register_agent(agent_id="bot_1", tenant_id="t1", name="Bot One", version="1.0.0")

    assert agent.agent_id == "bot_1"
    assert agent.status == AgentStatus.ACTIVE
    assert agent.tenant_id == "t1"

    fetched = svc.get_agent("bot_1")
    assert fetched is not None
    assert fetched.name == "Bot One"

def test_agent_revocation(cp_container):
    svc: AgentService = cp_container.agent_service
    svc.register_agent(agent_id="bot_2", tenant_id="t1", name="Bot Two")

    revoked = svc.revoke_agent("bot_2", reason="Security vulnerability")
    assert revoked.status == AgentStatus.REVOKED
    assert revoked.revoked_at is not None

    # Revoked agent cannot receive bundle
    bundle_svc: BundleService = cp_container.bundle_service
    with pytest.raises(GuardWAFSecurityError) as exc_info:
        bundle_svc.compile_and_sign_bundle(tenant_id="t1", agent_id="bot_2")
    assert "REVOKED" in exc_info.value.message

def test_agent_tenant_isolation(cp_container):
    svc: AgentService = cp_container.agent_service
    svc.register_agent(agent_id="bot_t1", tenant_id="tenant_a", name="Tenant A Bot")

    bundle_svc: BundleService = cp_container.bundle_service
    with pytest.raises(GuardWAFSecurityError) as exc_info:
        bundle_svc.compile_and_sign_bundle(tenant_id="tenant_b", agent_id="bot_t1")
    assert "Tenant mismatch" in exc_info.value.message

# ============================================================================
# 2. POLICY VERSIONING & ROLLBACK TESTS
# ============================================================================

def test_policy_creation_versioning_and_rollback(cp_container):
    ps: PolicyService = cp_container.policy_service
    pol = ps.create_policy(tenant_id="t1", name="payment_policy")

    # Create Version 1
    v1_rules = {"bulk_thresholds": [{"tool": "pay", "param_name": "amount", "max_value": 100}]}
    ver1 = ps.create_version(pol.policy_id, rules=v1_rules)
    assert ver1.version_number == 1
    assert ver1.content_digest is not None

    # Create Version 2
    v2_rules = {"bulk_thresholds": [{"tool": "pay", "param_name": "amount", "max_value": 500}]}
    ver2 = ps.create_version(pol.policy_id, rules=v2_rules)
    assert ver2.version_number == 2

    # Activate Version 2
    ps.publish_and_activate(pol.policy_id, version_number=2)
    updated = cp_container.repo.get_policy(pol.policy_id)
    assert updated.active_version == 2
    assert updated.status == PolicyStatus.ACTIVE

    # Rollback to Version 1
    rolled_back = ps.rollback_version(pol.policy_id, target_version_number=1)
    assert rolled_back.active_version == 1

# ============================================================================
# 3. SIGNED POLICY BUNDLE & TAMPERING TESTS
# ============================================================================

def test_signed_policy_bundle_compilation_and_verification(cp_container):
    agent_svc: AgentService = cp_container.agent_service
    policy_svc: PolicyService = cp_container.policy_service
    bundle_svc: BundleService = cp_container.bundle_service

    agent_svc.register_agent("agent_bundle_1", "t1", "Agent 1")
    pol = policy_svc.create_policy("t1", "transfer_policy")
    policy_svc.create_version(pol.policy_id, rules={"bulk_thresholds": [{"tool": "transfer", "param_name": "val", "max_value": 50}]})
    policy_svc.publish_and_activate(pol.policy_id, version_number=1)
    policy_svc.assign_policy(tenant_id="t1", policy_id=pol.policy_id, agent_id="agent_bundle_1")

    bundle = bundle_svc.compile_and_sign_bundle(tenant_id="t1", agent_id="agent_bundle_1")
    assert bundle.bundle_digest is not None
    assert bundle.signature is not None

    # Verification should succeed
    is_valid = bundle_svc.verify_bundle_signature(bundle)
    assert is_valid is True

def test_tampered_bundle_rejection(cp_container):
    agent_svc: AgentService = cp_container.agent_service
    policy_svc: PolicyService = cp_container.policy_service
    bundle_svc: BundleService = cp_container.bundle_service

    agent_svc.register_agent("agent_tamper", "t1", "Agent Tamper")
    pol = policy_svc.create_policy("t1", "p1")
    policy_svc.create_version(pol.policy_id, rules={"bulk_thresholds": []})
    policy_svc.publish_and_activate(pol.policy_id, 1)
    policy_svc.assign_policy(tenant_id="t1", policy_id=pol.policy_id, agent_id="agent_tamper")

    valid_bundle = bundle_svc.compile_and_sign_bundle(tenant_id="t1", agent_id="agent_tamper")

    # Tamper with payload
    tampered_bundle = SignedPolicyBundle.model_validate(valid_bundle.model_dump())
    tampered_bundle.policy_payload["shadow_mode"] = True

    # Verification must fail!
    assert bundle_svc.verify_bundle_signature(tampered_bundle) is False

# ============================================================================
# 4. SDK POLICY CLIENT & HOT-PATH LATENCY TESTS
# ============================================================================

def test_sdk_policy_client_lkg_fallback_and_latency(cp_container):
    agent_svc: AgentService = cp_container.agent_service
    policy_svc: PolicyService = cp_container.policy_service
    bundle_svc: BundleService = cp_container.bundle_service

    agent_svc.register_agent("sdk_bot", "tenant_x", "SDK Bot")
    pol = policy_svc.create_policy("tenant_x", "sdk_pol")
    policy_svc.create_version(pol.policy_id, rules={"bulk_thresholds": [{"tool": "execute_task", "param_name": "cost", "max_value": 10}]})
    policy_svc.publish_and_activate(pol.policy_id, 1)
    policy_svc.assign_policy("tenant_x", pol.policy_id, agent_id="sdk_bot")

    policy_client = PolicyClient(
        tenant_id="tenant_x",
        agent_id="sdk_bot",
        bundle_service=bundle_svc,
        mode=PolicyClientMode.GRACE_PERIOD
    )

    # Initial fetch
    success = policy_client.fetch_and_apply_remote()
    assert success is True

    # Measure Local Hot Path Policy Evaluation Latency
    start_ts = time.time()
    active_policy = policy_client.get_active_policy()
    latency_ms = (time.time() - start_ts) * 1000

    assert active_policy is not None
    assert latency_ms < 1.0  # Verified under 1ms target!

    # Simulate Control Plane Outage -> Fails remote fetch but retains LKG policy
    policy_client.set_bundle_fetcher(lambda: None)  # Return None or fail
    refreshed = policy_client.fetch_and_apply_remote()
    assert refreshed is False

    # LKG Policy remains valid and active
    lkg_policy = policy_client.get_active_policy()
    assert lkg_policy is not None

# ============================================================================
# 5. FASTAPI CONTROL PLANE ENDPOINT TESTS
# ============================================================================

def test_fastapi_control_plane_endpoints(api_client):
    # Health
    res = api_client.get("/health")
    assert res.status_code == 200
    assert res.json()["status"] == "HEALTHY"

    # Create Agent
    agent_res = api_client.post("/api/v1/agents", json={
        "agent_id": "api_agent_1",
        "tenant_id": "tenant_api",
        "name": "API Agent"
    })
    assert agent_res.status_code == 200
    assert agent_res.json()["agent_id"] == "api_agent_1"

    # Create Policy
    pol_res = api_client.post("/api/v1/policies", json={
        "tenant_id": "tenant_api",
        "name": "api_policy"
    })
    assert pol_res.status_code == 200
    policy_id = pol_res.json()["policy_id"]

    # Create Version
    ver_res = api_client.post(f"/api/v1/policies/{policy_id}/versions", json={
        "rules": {"sequences": []}
    })
    assert ver_res.status_code == 200

    # Activate
    act_res = api_client.post(f"/api/v1/policies/{policy_id}/activate", json={"version_number": 1})
    assert act_res.status_code == 200

    # Assign
    api_client.post("/api/v1/policies/assignments", json={
        "tenant_id": "tenant_api",
        "policy_id": policy_id,
        "agent_id": "api_agent_1"
    })

    # Compile Bundle
    bundle_res = api_client.post("/api/v1/bundles/compile", json={
        "tenant_id": "tenant_api",
        "agent_id": "api_agent_1"
    })
    assert bundle_res.status_code == 200
    assert "signature" in bundle_res.json()

    # Audit Events
    audit_res = api_client.get("/api/v1/audit/tenant_api")
    assert audit_res.status_code == 200
    assert len(audit_res.json()) >= 3
