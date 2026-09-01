"""
Phase 7 Backward Compatibility & Guarantee Preservation Test Suite.
Verifies that all Phase 1-6 APIs, decorators, ActionEnvelopes, and state stores operate without breaking changes.
"""

import pytest

from guardwaf import GuardWAF, GuardWAFSecurityError, protect
from guardwaf.core.models import BulkThresholdRule, PolicyConfig, PolicyRules


def test_legacy_phase1_decorator_compatibility():
    rules = PolicyRules(
        bulk_thresholds=[
            BulkThresholdRule(tool="legacy_func", param_name="val", max_value=10)
        ]
    )
    policy = PolicyConfig(metadata={"policy_name": "legacy_p"}, rules=rules)
    waf = GuardWAF(policy=policy, secret_key="legacy_compat_secret_key_32bytes_long")

    @protect(tool_name="legacy_func", client=waf)
    def legacy_func(val: int):
        return val

    with waf.session(session_id="sess_legacy"):
        assert legacy_func(val=5) == 5
        with pytest.raises(GuardWAFSecurityError):
            legacy_func(val=50)
