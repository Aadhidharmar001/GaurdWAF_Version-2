"""
Unit Tests for P0 Security Fixes: Production Secret Key Enforcement & Key Rotation.
"""

import os
import pytest
from guardwaf import (
    GuardWAF,
    protect,
    session,
    GuardWAFConfigurationError,
    GuardWAFHITLRequiredError
)

def test_production_mode_refuses_default_key(monkeypatch):
    # Ensure environment variable is clear
    monkeypatch.delenv("GUARDWAF_SECRET_KEY", raising=False)

    # 1. Direct argument environment="production" without secret_key MUST FAIL
    with pytest.raises(GuardWAFConfigurationError) as exc:
        GuardWAF(config_path="rules.yaml", environment="production")
    assert "GUARDWAF_SECRET_KEY" in str(exc.value)

    # 2. Setting GUARDWAF_ENV="production" without secret_key MUST FAIL
    monkeypatch.setenv("GUARDWAF_ENV", "production")
    with pytest.raises(GuardWAFConfigurationError):
        GuardWAF(config_path="rules.yaml")

    # 3. Explicit default dev key in production MUST FAIL
    with pytest.raises(GuardWAFConfigurationError):
        GuardWAF(config_path="rules.yaml", environment="production", secret_key="gw_secret_default_development_key")

def test_production_mode_accepts_strong_custom_secret(monkeypatch):
    monkeypatch.setenv("GUARDWAF_ENV", "production")
    monkeypatch.setenv("GUARDWAF_SECRET_KEY", "prod_super_secret_key_123456789_xyz")

    # Should initialize cleanly in production with strong custom secret!
    waf = GuardWAF(config_path="rules.yaml")
    assert waf.key_manager.get_active_key()[1] == b"prod_super_secret_key_123456789_xyz"

@pytest.mark.asyncio
async def test_zero_downtime_key_rotation_with_keyring():
    # Phase 1: Sign approval token with Key V1 (key_id="k1")
    waf_v1 = GuardWAF(config_path="rules.yaml", key_id="k1", secret_key="secret_key_v1")

    @protect(tool_name="lookup_customer")
    def lookup_customer(customer_id: str):
        return {"status": "found"}

    @protect(tool_name="process_refund")
    def process_refund(customer_id: str, amount: float):
        return {"status": "SUCCESS"}

    with session(session_id="sess_rot_01", customer_id="cust_rot"):
        lookup_customer("cust_rot")
        try:
            process_refund("cust_rot", 250.0)
        except GuardWAFHITLRequiredError as e:
            pending_id = e.pending_action_id

    # Admin approves action under V1 key
    approved_v1 = waf_v1.approve_pending_action(pending_id)
    token_v1 = approved_v1.approval_token

    assert "hitl_apprv.k1." in token_v1

    # Phase 2: Key Rotation occurs on Server!
    # Active key updated to "k2" ("secret_key_v2"), but "k1" retained in keyring
    keyring = {
        "k1": "secret_key_v1",
        "k2": "secret_key_v2"
    }
    waf_v2 = GuardWAF(
        config_path="rules.yaml",
        key_id="k2",
        secret_key="secret_key_v2",
        keyring=keyring,
        state_store=waf_v1.state_store
    )
    # Re-register tools on new instance
    waf_v2.register_tool("lookup_customer", lookup_customer)
    waf_v2.register_tool("process_refund", process_refund)

    # Resume token issued under old key "k1" on new server instance running "k2"
    with session(session_id="sess_rot_01", customer_id="cust_rot"):
        res = await waf_v2.resume(pending_id, token_v1)
        assert res["status"] == "SUCCESS"
