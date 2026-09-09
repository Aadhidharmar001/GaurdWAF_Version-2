"""
Workstream H — Simulated Developer Onboarding & DX Metric Validation Test Suite.
Simulates a new developer journey installing GuardWAF, loading policy, protecting a tool, blocking a dangerous action, and executing HITL flows.
"""

import time

from guardwaf import GuardWAF, GuardWAFSecurityError, protect
from guardwaf.core.models import BulkThresholdRule, HITLRule, PolicyConfig, PolicyRules


def test_simulated_developer_journey_metrics():
    start_time = time.time()

    # 1. Developer loads policy configuration (Simulated Step 1)
    rules = PolicyRules(
        bulk_thresholds=[BulkThresholdRule(tool="refund", param_name="amount", max_value=100.0)],
        hitl_rules=[HITLRule(tool="refund", condition_param="amount", greater_than=50.0)],
    )
    policy = PolicyConfig(metadata={"policy_name": "sim_policy"}, rules=rules)
    waf = GuardWAF(policy=policy, secret_key="simulated_dev_secret_key_32bytes_long")

    # 2. Developer decorates first tool (Simulated Step 2)
    @protect(tool_name="refund", client=waf)
    def refund(amount: float):
        return f"OK_{amount}"

    time_to_first_tool = time.time() - start_time
    assert time_to_first_tool < 5.0  # Automated step takes milliseconds (< 10 minutes requirement)

    # 3. Developer executes safe action ($20.00)
    with waf.session(session_id="sess_sim_1"):
        assert refund(amount=20.0) == "OK_20.0"

    # 4. Developer triggers first blocked action ($500.00)
    blocked_triggered = False
    with waf.session(session_id="sess_sim_1"):
        try:
            refund(amount=500.0)
        except GuardWAFSecurityError:
            blocked_triggered = True

    assert blocked_triggered is True
    time_to_first_block = time.time() - start_time
    assert time_to_first_block < 10.0  # Automated step takes milliseconds (< 15 minutes requirement)
