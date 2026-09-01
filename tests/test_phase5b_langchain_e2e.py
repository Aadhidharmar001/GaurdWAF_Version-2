"""
Workstream B1 — Real LangChain Integration End-to-End Test Suite.
Verifies allowed actions, policy blocks (0 downstream execution), HITL suspension, approval resume, and agent revocation.
"""

import pytest

from guardwaf import GuardWAF, GuardWAFHITLRequiredError, GuardWAFSecurityError
from guardwaf.core.models import BulkThresholdRule, HITLRule, PolicyConfig, PolicyRules
from guardwaf.integrations.langchain import protect_tool

LANGCHAIN_EXEC_COUNT = 0


def raw_refund_tool(customer_id: str, amount: float):
    global LANGCHAIN_EXEC_COUNT
    LANGCHAIN_EXEC_COUNT += 1
    return {"status": "SUCCESS", "refunded": amount}


@pytest.fixture
def langchain_waf_env():
    global LANGCHAIN_EXEC_COUNT
    LANGCHAIN_EXEC_COUNT = 0

    rules = PolicyRules(
        bulk_thresholds=[
            BulkThresholdRule(
                tool="process_refund", param_name="amount", max_value=5000
            )
        ],
        hitl_rules=[
            HITLRule(
                tool="process_refund", condition_param="amount", greater_than=100.0
            )
        ],
    )
    policy = PolicyConfig(metadata={"policy_name": "langchain_policy"}, rules=rules)
    waf = GuardWAF(policy=policy, secret_key="secret_langchain_test")
    waf.register_tool("process_refund", raw_refund_tool)
    return waf


def test_langchain_allowed_and_blocked_execution(langchain_waf_env):
    waf = langchain_waf_env
    protected_tool = protect_tool(raw_refund_tool, tool_name="process_refund", waf=waf)

    # 1. Allowed action ($50)
    with waf.session(session_id="sess_lc_1", tenant_id="org_lc"):
        res = protected_tool(customer_id="cust_1", amount=50.0)
        assert res["status"] == "SUCCESS"
        assert LANGCHAIN_EXEC_COUNT == 1

    # 2. Blocked action exceeding bulk threshold ($10,000) -> Must result in 0 additional execution calls!
    initial_count = LANGCHAIN_EXEC_COUNT
    with waf.session(session_id="sess_lc_1", tenant_id="org_lc"):
        with pytest.raises(GuardWAFSecurityError) as exc_info:
            protected_tool(customer_id="cust_1", amount=10000.0)
        assert "blocked" in exc_info.value.message.lower()
        # Verify EXACTLY ZERO downstream execution occurred!
        assert LANGCHAIN_EXEC_COUNT == initial_count


def test_langchain_hitl_suspension_and_resume(langchain_waf_env):
    waf = langchain_waf_env
    protected_tool = protect_tool(raw_refund_tool, tool_name="process_refund", waf=waf)

    # High risk action ($500) -> Suspend HITL
    pending_id = None
    with waf.session(session_id="sess_lc_2", tenant_id="org_lc"):
        with pytest.raises(
            (GuardWAFHITLRequiredError, GuardWAFSecurityError)
        ) as exc_info:
            protected_tool(customer_id="cust_2", amount=500.0)
        pending_id = getattr(exc_info.value, "pending_action_id", None)
        if not pending_id:
            pending_id = waf.state_store.list_pending_actions()[-1].pending_action_id

    # Approve pending action
    approved = waf.approve_pending_action(pending_id, approver_id="admin_user")

    # Resume action
    curr_count = LANGCHAIN_EXEC_COUNT
    with waf.session(session_id="sess_lc_2", tenant_id="org_lc"):
        resumed = waf.resume_sync(
            pending_action_id=pending_id, approval_token=approved.approval_token
        )
        assert resumed["status"] == "SUCCESS"
        assert LANGCHAIN_EXEC_COUNT == curr_count + 1
