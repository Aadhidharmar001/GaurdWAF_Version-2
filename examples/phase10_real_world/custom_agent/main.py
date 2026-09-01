"""
Phase 10 Real-World Custom Agent Integration.
Governs pure Python custom agent loop tools via AgentRuntimeAdapter.
"""

import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from guardwaf import GuardWAF, GuardWAFSecurityError
from guardwaf.core.models import BulkThresholdRule, PolicyConfig, PolicyRules

execution_counter = 0


def raw_send_newsletter(recipient_count: int):
    global execution_counter
    execution_counter += 1
    return {"status": "SENT", "recipients": recipient_count}


def main():
    print(
        "=========================================================================================="
    )
    print("🛡️  PHASE 10 REAL-WORLD CUSTOM AGENT LOOP INTEGRATION")
    print(
        "=========================================================================================="
    )

    rules = PolicyRules(
        bulk_thresholds=[
            BulkThresholdRule(
                tool="send_newsletter", param_name="recipient_count", max_value=500
            )
        ]
    )
    waf = GuardWAF(
        policy=PolicyConfig(metadata={"policy_name": "custom_p10"}, rules=rules),
        secret_key="custom_p10_secret_key_32bytes_long",
    )

    waf.register_tool("send_newsletter", raw_send_newsletter)

    with waf.session(session_id="s_custom_p10"):
        # 1. Allowed Custom Loop Action
        envelope1 = waf.create_envelope("send_newsletter", {"recipient_count": 100})
        auth1 = waf.runtime_adapter.evaluate(envelope1)
        res1 = waf.execute_protected_action(
            auth1, raw_send_newsletter, recipient_count=100
        )
        print(f"▶ 1. Custom Agent Action (100 recipients): {res1}")

        # 2. Blocked Custom Loop Action -> 0 Executions
        print("\n▶ 2. Custom Agent Action (50,000 recipients)...")
        exec_before = execution_counter
        envelope2 = waf.create_envelope("send_newsletter", {"recipient_count": 50000})
        try:
            auth2 = waf.runtime_adapter.evaluate(envelope2)
            waf.execute_protected_action(
                auth2, raw_send_newsletter, recipient_count=50000
            )
        except GuardWAFSecurityError as err:
            print(f"   🚨 BLOCKED CUSTOM AGENT ACTION: {err}")

        exec_after = execution_counter
        assert exec_before == exec_after
        print(
            f"   🔒 Downstream Custom Executions After Block: {exec_after} (Delta: 0)"
        )

    print(
        "=========================================================================================="
    )
    print("✅ CUSTOM AGENT REAL-WORLD INTEGRATION COMPLETE!")
    print(
        "=========================================================================================="
    )


if __name__ == "__main__":
    main()
