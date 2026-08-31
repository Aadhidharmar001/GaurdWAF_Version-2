"""
Comprehensive Unit Test Suite for Phase 3A Trusted Identity & Delegated Authority Boundary.
"""

import pytest
import asyncio
import jwt
from datetime import datetime, timedelta, timezone
from guardwaf import (
    GuardWAF,
    protect,
    session,
    verified_session,
    VerifiedPrincipal,
    AgentIdentity,
    DelegatedAuthority,
    JWTIdentityProvider,
    StaticIdentityProvider,
    IdentityCredentials,
    GuardWAFSecurityError,
    GuardWAFAuthorizationError,
    GuardWAFAuthenticationError,
    GuardWAFAuthorityExpiredError,
    GuardWAFTenantBoundaryError,
    GuardWAFInvalidTokenError,
    GuardWAFUnverifiedContextError,
)

@pytest.fixture
def waf_client():
    return GuardWAF(config_path="rules.yaml")

@pytest.fixture
def strict_waf_client():
    return GuardWAF(config_path="rules.yaml", strict_identity=True)

# --- 1. Identity & Context Tests ---

def test_immutable_verified_principal():
    principal = VerifiedPrincipal(
        principal_id="usr_100",
        tenant_id="tenant_a",
        subject="auth0|100",
        roles=["admin"]
    )
    with pytest.raises(Exception):
        principal.principal_id = "hacked_id"  # Immutable Pydantic model

def test_strict_mode_rejects_unverified_context(strict_waf_client):
    @protect(tool_name="lookup_customer")
    def lookup_customer(customer_id: str):
        return {"status": "ok"}

    # Running without verified_session in strict mode MUST FAIL
    with pytest.raises(GuardWAFUnverifiedContextError):
        lookup_customer("cust_123")

# --- 2. JWT Cryptographic Verification Tests ---

def test_jwt_provider_cryptographic_verification():
    secret = "super_secret_jwt_test_key_32bytes_long!"
    provider = JWTIdentityProvider(
        secret_key=secret,
        issuer="https://auth.example.com/",
        audience="guardwaf-api"
    )

    # Valid Token
    payload = {
        "sub": "usr_jwt_123",
        "tenant_id": "tenant_acme",
        "iss": "https://auth.example.com/",
        "aud": "guardwaf-api",
        "roles": ["support"],
        "exp": int((datetime.now(timezone.utc) + timedelta(hours=1)).timestamp())
    }
    valid_token = jwt.encode(payload, secret, algorithm="HS256")
    principal = provider.authenticate(IdentityCredentials(raw_token=valid_token))
    assert principal.principal_id == "usr_jwt_123"
    assert principal.tenant_id == "tenant_acme"

    # Forged Token
    forged_token = valid_token[:-6] + "BADSIG"
    with pytest.raises(GuardWAFInvalidTokenError):
        provider.authenticate(IdentityCredentials(raw_token=forged_token))

    # Expired Token
    exp_payload = dict(payload)
    exp_payload["exp"] = int((datetime.now(timezone.utc) - timedelta(seconds=10)).timestamp())
    exp_token = jwt.encode(exp_payload, secret, algorithm="HS256")
    with pytest.raises(GuardWAFAuthenticationError):
        provider.authenticate(IdentityCredentials(raw_token=exp_token))

    # Issuer Mismatch
    bad_iss_payload = dict(payload)
    bad_iss_payload["iss"] = "https://evil.com/"
    bad_iss_token = jwt.encode(bad_iss_payload, secret, algorithm="HS256")
    with pytest.raises(GuardWAFAuthenticationError):
        provider.authenticate(IdentityCredentials(raw_token=bad_iss_token))

    # alg=none prohibited
    alg_none_token = jwt.encode(payload, "", algorithm="none")
    with pytest.raises(GuardWAFInvalidTokenError):
        provider.authenticate(IdentityCredentials(raw_token=alg_none_token))

# --- 3. Delegated Authority Boundary Tests ---

def test_delegated_authority_tool_and_tenant_scope(waf_client):
    exec_count = 0

    @protect(tool_name="lookup_customer")
    def lookup_customer(customer_id: str):
        return {"status": "ok"}

    @protect(tool_name="process_refund")
    def process_refund(customer_id: str, amount: float):
        return {"status": "ok"}

    @protect(tool_name="delete_customer")
    def delete_customer(customer_id: str):
        nonlocal exec_count
        exec_count += 1
        return {"status": "deleted"}

    principal = VerifiedPrincipal(principal_id="usr_alice", tenant_id="tenant_acme", subject="alice")
    agent = AgentIdentity(agent_id="agent_v1", tenant_id="tenant_acme")
    authority = DelegatedAuthority(
        authority_id="auth_1",
        principal_id="usr_alice",
        agent_id="agent_v1",
        tenant_id="tenant_acme",
        allowed_actions=["lookup_customer", "process_refund"],
        constraints={"process_refund": {"max_amount": 100.0}},
        expires_at=datetime.now(timezone.utc) + timedelta(hours=1)
    )

    with verified_session(principal=principal, agent=agent, authority=authority):
        # 1. Allowed Tool & Sequence
        lookup_customer("cust_1")
        res = process_refund("cust_1", 50.0)
        assert res["status"] == "ok"

        # 2. Unauthorized Tool Attempt -> BLOCKED (0 Executions!)
        with pytest.raises(GuardWAFAuthorizationError):
            delete_customer("cust_1")

        assert exec_count == 0

        # 3. Delegated Limit Exceeded -> BLOCKED
        with pytest.raises(GuardWAFAuthorizationError):
            process_refund("cust_1", 250.0)

# --- 4. Tenant Boundary Anti-Spoofing Tests ---

def test_tenant_boundary_anti_spoofing(waf_client):
    @protect(tool_name="lookup_customer")
    def lookup_customer(customer_id: str):
        return {"status": "ok"}

    @protect(tool_name="process_refund")
    def process_refund(customer_id: str, amount: float, tenant_id: str = "tenant_a"):
        return {"status": "ok"}

    principal = VerifiedPrincipal(principal_id="usr_tenant", tenant_id="tenant_a", subject="usr")
    agent = AgentIdentity(agent_id="agent_a", tenant_id="tenant_a")
    authority = DelegatedAuthority(
        authority_id="auth_t",
        principal_id="usr_tenant",
        agent_id="agent_a",
        tenant_id="tenant_a",
        allowed_actions=["lookup_customer", "process_refund"],
        expires_at=datetime.now(timezone.utc) + timedelta(hours=1)
    )

    with verified_session(principal=principal, agent=agent, authority=authority):
        lookup_customer("cust_1")

        # Passing parameter tenant_id="tenant_victim" MUST BE BLOCKED by tenant boundary
        with pytest.raises(GuardWAFTenantBoundaryError):
            process_refund("cust_1", 50.0, tenant_id="tenant_victim")

# --- 5. Async Context Isolation Tests ---

@pytest.mark.asyncio
async def test_async_verified_session_context_isolation(waf_client):
    @protect(tool_name="lookup_customer")
    def lookup_customer(customer_id: str):
        return {"status": "ok"}

    p1 = VerifiedPrincipal(principal_id="usr_p1", tenant_id="t1", subject="p1")
    p2 = VerifiedPrincipal(principal_id="usr_p2", tenant_id="t2", subject="p2")

    async def worker_1():
        with verified_session(principal=p1):
            await asyncio.sleep(0.01)
            return lookup_customer("c1")

    async def worker_2():
        with verified_session(principal=p2):
            await asyncio.sleep(0.01)
            return lookup_customer("c2")

    res1, res2 = await asyncio.gather(worker_1(), worker_2())
    assert res1["status"] == "ok"
    assert res2["status"] == "ok"

# --- 6. ActionGrant Identity Binding Tests ---

def test_action_grant_identity_binding(waf_client):
    from guardwaf.core.models import ActionIntent

    intent = ActionIntent(
        intent_id="int_1",
        agent_id="agent_test",
        tool_name="test_tool",
        parameters={"val": 1},
        parameter_digest="digest_123"
    )

    grant = waf_client.signer.issue_grant(intent, delegated_authority_id="auth_999")
    assert grant.delegated_authority_id == "auth_999"
    assert waf_client.signer.verify_grant(grant, "digest_123") is True

    # Tampered parameter digest -> Fails verification
    assert waf_client.signer.verify_grant(grant, "digest_tampered") is False
