"""
GuardWAF LangChain Framework Integration Example.
Demonstrates securing LangChain tools via LangChainAdapter and ActionEnvelope.
"""

import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from guardwaf import GuardWAF, GuardWAFSecurityError
from guardwaf.core.models import BulkThresholdRule, PolicyConfig, PolicyRules
from guardwaf.integrations.langchain import DummyLangChainTool, LangChainAdapter


def raw_database_query(query: str, max_rows: int = 100):
    return {"status": "SUCCESS", "rows_returned": min(max_rows, 50), "query": query}


def main():
    print("=================================================================")
    print("🛡️  GUARdWAF LANGCHAIN FRAMEWORK INTEGRATION DEMO")
    print("=================================================================")

    rules = PolicyRules(
        bulk_thresholds=[
            BulkThresholdRule(tool="query_db", param_name="max_rows", max_value=500)
        ]
    )
    policy = PolicyConfig(metadata={"policy_name": "langchain_policy"}, rules=rules)
    waf = GuardWAF(policy=policy, secret_key="langchain_demo_secret_key_32bytes")

    # Wrap raw tool using LangChainAdapter
    adapter = LangChainAdapter(waf=waf)
    raw_tool = DummyLangChainTool(name="query_db", func=raw_database_query)
    protected_tool = adapter.wrap_tool(raw_tool)

    with waf.session(session_id="sess_lc_1"):
        # Safe call (max_rows=100)
        res1 = protected_tool.run(query="SELECT * FROM customers", max_rows=100)
        print(f"▶ 1. Safe LangChain Tool Execution: {res1}")

        # Dangerous call (max_rows=5,000)
        try:
            protected_tool.run(query="SELECT * FROM customers", max_rows=5000)
        except GuardWAFSecurityError as err:
            print(f"▶ 2. 🚨 BLOCKED LangChain Tool Execution: {err}")

    print("=================================================================")


if __name__ == "__main__":
    main()
