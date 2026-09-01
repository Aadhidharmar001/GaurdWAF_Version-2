"""
Unit Tests for Framework Adapters (LangChain, CrewAI, Custom Agent Adapter).
Verifies thin adapter translation, zero security logic duplication, and zero execution on block.
"""

import pytest

from guardwaf import GuardWAF
from guardwaf.core.keys import KeyManager
from guardwaf.core.models import BulkThresholdRule, PolicyConfig, PolicyRules
from guardwaf.exceptions import GuardWAFSecurityError
from guardwaf.integrations.crewai import protect_tool as protect_crewai_tool
from guardwaf.integrations.custom import CustomAgentAdapter
from guardwaf.integrations.langchain import protect_tool as protect_langchain_tool


@pytest.fixture
def setup_framework_waf():
    km = KeyManager(secret_key="dev_secret_key_framework_tests")
    rules = PolicyRules(
        bulk_thresholds=[
            BulkThresholdRule(
                tool="process_payment", param_name="amount", max_value=200
            )
        ]
    )
    policy = PolicyConfig(metadata={"policy_name": "framework_policy"}, rules=rules)
    return GuardWAF(policy=policy, secret_key="dev_secret_key_framework_tests")


def test_custom_agent_adapter(setup_framework_waf):
    waf = setup_framework_waf
    adapter = CustomAgentAdapter(waf=waf)

    call_count = {"count": 0}

    def pay_func(amount: float, **kwargs):
        call_count["count"] += 1
        return "PAID"

    protected_pay = adapter.wrap_tool(pay_func, tool_name="process_payment")

    # Allowed ($100 <= $200)
    res = protected_pay(amount=100.0)
    assert res == "PAID"
    assert call_count["count"] == 1

    # Blocked ($300 > $200)
    with pytest.raises(GuardWAFSecurityError):
        protected_pay(amount=300.0)
    assert call_count["count"] == 1  # Zero additional executions!


def test_langchain_adapter(setup_framework_waf):
    waf = setup_framework_waf
    call_count = {"count": 0}

    def pay_func(amount: float, **kwargs):
        call_count["count"] += 1
        return "PAID"

    lc_tool = protect_langchain_tool(pay_func, waf=waf, tool_name="process_payment")

    # Allowed
    res = lc_tool.run(amount=150.0)
    assert call_count["count"] == 1

    # Blocked
    with pytest.raises(GuardWAFSecurityError):
        lc_tool.run(amount=500.0)
    assert call_count["count"] == 1


def test_crewai_adapter(setup_framework_waf):
    waf = setup_framework_waf
    call_count = {"count": 0}

    def pay_func(amount: float, **kwargs):
        call_count["count"] += 1
        return "PAID"

    crew_tool = protect_crewai_tool(pay_func, waf=waf, tool_name="process_payment")

    # Allowed
    res = crew_tool._run(amount=50.0)
    assert call_count["count"] == 1

    # Blocked
    with pytest.raises(GuardWAFSecurityError):
        crew_tool._run(amount=900.0)
    assert call_count["count"] == 1
