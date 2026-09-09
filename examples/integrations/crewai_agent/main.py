"""
GuardWAF CrewAI Framework Integration Example.
Demonstrates securing CrewAI agent tasks and tools via CrewAIAdapter.
"""

import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from guardwaf import GuardWAF, GuardWAFSecurityError
from guardwaf.core.models import BulkThresholdRule, PolicyConfig, PolicyRules
from guardwaf.integrations.crewai import protect_crewai_tool


def send_marketing_email(recipient_count: int, subject: str):
    return {"status": "SUCCESS", "sent_count": recipient_count}


def main():
    print("=================================================================")
    print("🛡️  GUARdWAF CREWAI FRAMEWORK INTEGRATION DEMO")
    print("=================================================================")

    rules = PolicyRules(bulk_thresholds=[BulkThresholdRule(tool="send_email", param_name="recipient_count", max_value=100)])
    policy = PolicyConfig(metadata={"policy_name": "crewai_policy"}, rules=rules)
    waf = GuardWAF(policy=policy, secret_key="crewai_demo_secret_key_32bytes_long")

    protected_crew_tool = protect_crewai_tool(send_marketing_email, waf=waf, tool_name="send_email")

    with waf.session(session_id="sess_crew_1"):
        res1 = protected_crew_tool(recipient_count=20, subject="Weekly Digest")
        print(f"▶ 1. Safe CrewAI Tool Execution: {res1}")

        try:
            protected_crew_tool(recipient_count=5000, subject="SPAM Blast")
        except GuardWAFSecurityError as err:
            print(f"▶ 2. 🚨 BLOCKED CrewAI Tool Execution: {err}")

    print("=================================================================")


if __name__ == "__main__":
    main()
