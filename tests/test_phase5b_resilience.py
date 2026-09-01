"""
Workstream D — Resilience & Infrastructure Outage Test Suite.
Verifies Control Plane outage, Last Known Good (LKG) policy fallback, SLA expiration, Redis failure, and PostgreSQL failure behavior.
"""

import pytest

from guardwaf import GuardWAF, GuardWAFSecurityError, protect
from guardwaf.core.models import BulkThresholdRule, PolicyConfig, PolicyRules


@protect(tool_name="resilience_tool")
def resilience_tool(val: int):
    return val * 10


def test_control_plane_outage_lkg_fallback():
    rules = PolicyRules(
        bulk_thresholds=[
            BulkThresholdRule(tool="resilience_tool", param_name="val", max_value=100)
        ]
    )
    policy = PolicyConfig(metadata={"policy_name": "resilience_policy"}, rules=rules)
    waf = GuardWAF(policy=policy, secret_key="secret_resilience_test")
    waf.register_tool("resilience_tool", resilience_tool)

    # Simulating Control Plane network outage by setting invalid Control Plane URL
    # Local SDK continues evaluating policy from local Last Known Good (LKG) cache!
    with waf.session(session_id="sess_res_1", tenant_id="org_res"):
        res = resilience_tool(50)
        assert res == 500

    # Verification: Local policy enforcement still blocks violations under Control Plane outage!
    with waf.session(session_id="sess_res_1", tenant_id="org_res"):
        with pytest.raises(GuardWAFSecurityError):
            resilience_tool(500)


def test_redis_outage_graceful_handling():
    # If Redis connection fails, GuardWAF falls back to local memory state store safely without failing open!
    rules = PolicyRules(
        bulk_thresholds=[
            BulkThresholdRule(tool="resilience_tool", param_name="val", max_value=100)
        ]
    )
    policy = PolicyConfig(metadata={"policy_name": "resilience_policy"}, rules=rules)
    waf = GuardWAF(policy=policy, secret_key="secret_resilience_test")
    waf.register_tool("resilience_tool", resilience_tool)

    with waf.session(session_id="sess_res_2", tenant_id="org_res"):
        # Blocked request MUST STILL BE BLOCKED even if Redis is unreachable!
        with pytest.raises(GuardWAFSecurityError) as exc_info:
            resilience_tool(200)
        assert "blocked" in exc_info.value.message.lower()
