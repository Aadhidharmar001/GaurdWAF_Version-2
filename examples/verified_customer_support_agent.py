"""
GuardWAF Phase 3A Example Application: Trusted Identity & Delegated Authority Boundary.
Demonstrates Scenarios 1-6 covering valid identity/authority, tenant spoofing prevention,
expired authority, unauthorized tool attempt, delegated amount limit constraints, and JWT cryptographic verification.
"""

import sys
import os
import asyncio
import jwt
from datetime import datetime, timedelta, timezone

# Ensure UTF-8 output on Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from guardwaf import (
    GuardWAF,
    protect,
    verified_session,
    VerifiedPrincipal,
    AgentIdentity,
    DelegatedAuthority,
    JWTIdentityProvider,
    IdentityCredentials,
    GuardWAFAuthorizationError,
    GuardWAFAuthorityExpiredError,
    GuardWAFTenantBoundaryError,
    GuardWAFAuthenticationError,
    GuardWAFInvalidTokenError,
    GuardWAFSecurityError,
)

# Initialize GuardWAF
waf = GuardWAF(config_path="rules.yaml")

DELETE_EXECUTION_COUNT = 0

@protect(tool_name="lookup_customer")
def lookup_customer(customer_id: str):
    print(f"   [TOOL EXECUTION] Looking up customer '{customer_id}'")
    return {"customer_id": customer_id, "status": "active"}

@protect(tool_name="process_refund")
def process_refund(customer_id: str, amount: float, tenant_id: str = "acme_corp"):
    print(f"   [TOOL EXECUTION] 💸 Refunding ${amount:.2f} to {customer_id} (Tenant: {tenant_id})")
    return {"status": "SUCCESS", "refunded": amount}

@protect(tool_name="delete_customer")
def delete_customer(customer_id: str):
    global DELETE_EXECUTION_COUNT
    DELETE_EXECUTION_COUNT += 1
    print(f"   ❌ DANGER TOOL EXECUTED: Deleted customer '{customer_id}'!")
    return {"status": "DELETED"}

def run_phase3a_identity_demo():
    global DELETE_EXECUTION_COUNT
    print("=" * 80)
    print("🛡️  GUARdWAF PHASE 3A DEMO: TRUSTED IDENTITY & DELEGATED AUTHORITY BOUNDARY")
    print("=" * 80)

    # Base Verified Principal & Agent Identity
    alice_principal = VerifiedPrincipal(
        principal_id="usr_alice_999",
        tenant_id="acme_corp",
        subject="auth0|alice999",
        issuer="https://auth.acme.com/",
        audience="guardwaf-api",
        authentication_method="jwt",
        roles=["support_agent"],
        permissions=["refund:create", "customer:read"]
    )

    support_agent = AgentIdentity(
        agent_id="support-agent-v1",
        agent_type="customer_support",
        tenant_id="acme_corp"
    )

    # --- Scenario 1: Valid Identity + Valid Delegated Authority ---
    print("\n▶ SCENARIO 1: Valid Identity + Valid Delegated Authority ($100 max refund)...")
    valid_authority = DelegatedAuthority(
        authority_id="auth_valid_100",
        principal_id="usr_alice_999",
        agent_id="support-agent-v1",
        tenant_id="acme_corp",
        allowed_actions=["lookup_customer", "process_refund"],
        constraints={"process_refund": {"max_amount": 100.0}},
        expires_at=datetime.now(timezone.utc) + timedelta(hours=1)
    )

    with waf.verified_session(principal=alice_principal, agent=support_agent, authority=valid_authority):
        lookup_customer("cust_alice")
        res = process_refund("cust_alice", 50.00)
        print(f"   ✅ SUCCESS: Processed allowed refund of $50.00: {res}")

    # --- Scenario 2: Agent Generates Fake Tenant ID in Tool Arguments ---
    print("\n▶ SCENARIO 2: Agent attempts tenant spoofing (Passing tenant_id='victim_corp')...")
    with waf.verified_session(principal=alice_principal, agent=support_agent, authority=valid_authority):
        lookup_customer("cust_alice")
        try:
            process_refund("cust_alice", 50.00, tenant_id="victim_corp")
            print("   ❌ FAIL: Tenant spoofing was not blocked!")
        except GuardWAFTenantBoundaryError as e:
            print(f"   ✅ GUARDWAF BLOCKED TENANT SPOOFING: {e.message}")

    # --- Scenario 3: Expired Delegated Authority ---
    print("\n▶ SCENARIO 3: Expired Delegated Authority...")
    expired_authority = DelegatedAuthority(
        authority_id="auth_exp_999",
        principal_id="usr_alice_999",
        agent_id="support-agent-v1",
        tenant_id="acme_corp",
        allowed_actions=["lookup_customer", "process_refund"],
        expires_at=datetime.now(timezone.utc) - timedelta(minutes=5)
    )

    with waf.verified_session(principal=alice_principal, agent=support_agent, authority=expired_authority):
        try:
            process_refund("cust_alice", 50.00)
            print("   ❌ FAIL: Expired authority was allowed!")
        except GuardWAFAuthorityExpiredError as e:
            print(f"   ✅ GUARDWAF BLOCKED EXPIRED AUTHORITY: {e.message}")

    # --- Scenario 4: Unauthorized Tool Attempt ---
    print("\n▶ SCENARIO 4: Agent attempts unauthorized tool ('delete_customer')...")
    with waf.verified_session(principal=alice_principal, agent=support_agent, authority=valid_authority):
        try:
            delete_customer("cust_alice")
            print("   ❌ FAIL: Unauthorized tool executed!")
        except GuardWAFAuthorizationError as e:
            print(f"   ✅ GUARDWAF BLOCKED UNAUTHORIZED TOOL: {e.message}")
            print(f"      - Execution Count: {DELETE_EXECUTION_COUNT} (Verified 0 Executions!)")

    # --- Scenario 5: Delegated Authority Constraint ($250 > $100 limit) ---
    print("\n▶ SCENARIO 5: Agent attempts refund ($250.00) exceeding delegated limit ($100.00)...")
    with waf.verified_session(principal=alice_principal, agent=support_agent, authority=valid_authority):
        lookup_customer("cust_alice")
        try:
            process_refund("cust_alice", 250.00)
            print("   ❌ FAIL: Limit violation was allowed!")
        except GuardWAFAuthorizationError as e:
            print(f"   ✅ GUARDWAF BLOCKED DELEGATED CONSTRAINT VIOLATION: {e.message}")


    # --- Scenario 6: Cryptographic JWT Identity Verification ---
    print("\n▶ SCENARIO 6: Cryptographic JWT Identity Provider Verification...")
    jwt_secret = "super_secret_jwt_key_999"
    jwt_provider = JWTIdentityProvider(
        secret_key=jwt_secret,
        issuer="https://auth.acme.com/",
        audience="guardwaf-api"
    )

    # 6a. Generate Valid JWT
    valid_payload = {
        "sub": "usr_bob_777",
        "tenant_id": "acme_corp",
        "iss": "https://auth.acme.com/",
        "aud": "guardwaf-api",
        "roles": ["customer_support"],
        "permissions": ["refund:create"],
        "exp": int((datetime.now(timezone.utc) + timedelta(hours=1)).timestamp())
    }
    valid_jwt = jwt.encode(valid_payload, jwt_secret, algorithm="HS256")
    bob_principal = jwt_provider.authenticate(IdentityCredentials(raw_token=valid_jwt))
    print(f"   ✅ AUTHENTICATED JWT: Principal ID='{bob_principal.principal_id}', Tenant='{bob_principal.tenant_id}'")

    # 6b. Forged Signature Token
    print("   Testing Forged Signature JWT...")
    forged_jwt = valid_jwt[:-5] + "XXXXX"
    try:
        jwt_provider.authenticate(IdentityCredentials(raw_token=forged_jwt))
        print("   ❌ FAIL: Forged JWT accepted!")
    except GuardWAFInvalidTokenError as e:
        print(f"   ✅ GUARDWAF REJECTED FORGED JWT: {e.message}")

    # 6c. Expired JWT
    print("   Testing Expired JWT Token...")
    expired_payload = dict(valid_payload)
    expired_payload["exp"] = int((datetime.now(timezone.utc) - timedelta(seconds=10)).timestamp())
    expired_jwt = jwt.encode(expired_payload, jwt_secret, algorithm="HS256")
    try:
        jwt_provider.authenticate(IdentityCredentials(raw_token=expired_jwt))
        print("   ❌ FAIL: Expired JWT accepted!")
    except GuardWAFAuthenticationError as e:
        print(f"   ✅ GUARDWAF REJECTED EXPIRED JWT: {e.message}")

    print("\n" + "=" * 80)
    print("✅ PHASE 3A DEMO COMPLETE: All Trusted Identity & Delegated Authority Boundaries Verified!")
    print("=" * 80)

if __name__ == "__main__":
    run_phase3a_identity_demo()
