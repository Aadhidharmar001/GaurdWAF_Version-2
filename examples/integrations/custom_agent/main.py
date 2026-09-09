"""
GuardWAF Custom Python Agent Framework Integration Example.
Demonstrates securing custom Python LLM agent loops via AgentRuntimeAdapter.
"""

import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from guardwaf import GuardWAF
from guardwaf.core.action_envelope import ActionEnvelope
from guardwaf.core.models import BulkThresholdRule, PolicyConfig, PolicyRules


def raw_execute_trade(ticker: str, shares: int):
    return {"status": "SUCCESS", "ticker": ticker, "shares": shares}


def main():
    print("=================================================================")
    print("🛡️  GUARdWAF CUSTOM PYTHON AGENT INTEGRATION DEMO")
    print("=================================================================")

    rules = PolicyRules(bulk_thresholds=[BulkThresholdRule(tool="execute_trade", param_name="shares", max_value=100)])
    policy = PolicyConfig(metadata={"policy_name": "custom_agent_policy"}, rules=rules)
    waf = GuardWAF(policy=policy, secret_key="custom_demo_secret_key_32bytes_long")

    with waf.session(session_id="sess_custom_1"):
        # Create ActionEnvelope for custom loop
        env_safe = ActionEnvelope(
            tenant_id="default",
            agent_id="trading_bot",
            session_id="sess_custom_1",
            tool_name="execute_trade",
            parameters={"ticker": "AAPL", "shares": 10},
        )

        decision1 = waf.runtime_adapter.evaluate(env_safe)
        if decision1.allowed:
            res1 = raw_execute_trade(ticker="AAPL", shares=10)
            print(f"▶ 1. Safe Custom Agent Action: {res1}")

        env_danger = ActionEnvelope(
            tenant_id="default",
            agent_id="trading_bot",
            session_id="sess_custom_1",
            tool_name="execute_trade",
            parameters={"ticker": "AAPL", "shares": 5000},
        )
        decision2 = waf.runtime_adapter.evaluate(env_danger)
        if not decision2.allowed:
            print(f"▶ 2. 🚨 BLOCKED Custom Agent Action: {decision2.reason}")

    print("=================================================================")


if __name__ == "__main__":
    main()
