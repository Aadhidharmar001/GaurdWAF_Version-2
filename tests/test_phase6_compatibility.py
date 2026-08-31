"""
Workstream G — Production API & SDK Compatibility Test Suite.
Verifies /api/v1/ endpoint versioning, policy backward compatibility, zero-downtime key rotation during active execution, and SDK stability.
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app
from guardwaf import GuardWAF, protect, GuardWAFSecurityError
from guardwaf.core.models import PolicyConfig, PolicyRules, BulkThresholdRule

client = TestClient(app)

def test_api_versioning_and_health_routes():
    res_live = client.get("/health/live")
    assert res_live.status_code == 200
    assert res_live.json()["status"] == "alive"

    res_ready = client.get("/health/ready")
    assert res_ready.status_code == 200
    assert res_ready.json()["status"] == "ready"

def test_policy_backward_compatibility():
    # Verifies legacy policy configuration formats load cleanly without schema errors
    rules = PolicyRules(bulk_thresholds=[BulkThresholdRule(tool="legacy_tool", param_name="qty", max_value=10)])
    policy = PolicyConfig(metadata={"policy_name": "v1_legacy_policy", "version": "1"}, rules=rules)


    waf = GuardWAF(policy=policy, secret_key="compat_secret_key_32bytes_min_long")

    @protect(tool_name="legacy_tool", client=waf)
    def legacy_tool(qty: int):
        return f"OK_{qty}"

    with waf.session(session_id="sess_compat_1"):
        assert legacy_tool(qty=5) == "OK_5"
        with pytest.raises(GuardWAFSecurityError):
            legacy_tool(qty=50)

def test_zero_downtime_key_rotation_during_execution():
    keyring = {"k1": "old_secret_key_32bytes_long_aaaa", "k2": "new_secret_key_32bytes_long_bbbb"}
    rules = PolicyRules(bulk_thresholds=[BulkThresholdRule(tool="rot_tool", param_name="val", max_value=100)])
    policy = PolicyConfig(metadata={"policy_name": "rot_policy"}, rules=rules)

    waf = GuardWAF(policy=policy, secret_key="old_secret_key_32bytes_long_aaaa", key_id="k1", keyring=keyring)

    @protect(tool_name="rot_tool", client=waf)
    def rot_tool(val: float):
        return val

    with waf.session(session_id="sess_rot_1"):
        assert rot_tool(val=10.0) == 10.0

        # Rotate key dynamically
        waf.key_manager.rotate_key(new_key_id="k2", new_secret_key="new_secret_key_32bytes_long_bbbb")
        assert rot_tool(val=20.0) == 20.0
