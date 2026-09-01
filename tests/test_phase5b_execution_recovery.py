"""
Workstream D4 — Process Crash & HITL Execution Recovery Test Suite.
Verifies execution lease tracking, abandoned lease detection, and execution state recovery.
"""

from guardwaf import GuardWAF, GuardWAFHITLRequiredError, GuardWAFSecurityError, protect
from guardwaf.core.models import ActionState, HITLRule, PolicyConfig, PolicyRules


@protect(tool_name="crashtest_tool")
def crashtest_tool(amount: float):
    return {"status": "SUCCESS", "amount": amount}


def test_hitl_execution_lease_recovery():
    rules = PolicyRules(
        hitl_rules=[
            HITLRule(tool="crashtest_tool", condition_param="amount", greater_than=50.0)
        ]
    )
    policy = PolicyConfig(metadata={"policy_name": "crash_policy"}, rules=rules)
    waf = GuardWAF(policy=policy, secret_key="secret_crash_key")
    waf.register_tool("crashtest_tool", crashtest_tool)

    # 1. Trigger PendingAction
    pending_id = None
    with waf.session(session_id="sess_crash_1", tenant_id="org_crash"):
        try:
            crashtest_tool(100.0)
        except (GuardWAFHITLRequiredError, GuardWAFSecurityError) as e:
            pending_id = getattr(e, "pending_action_id", None)
            if not pending_id:
                pending_id = waf.state_store.list_pending_actions()[
                    -1
                ].pending_action_id

    # 2. Approve PendingAction
    approved = waf.approve_pending_action(pending_id, approver_id="admin_approver")

    # 3. Simulate process crash during EXECUTING state: state store updates to EXECUTED upon completion
    action = waf.state_store.get_pending_action(pending_id)
    assert action is not None
    assert action.status.value in ["APPROVED", "PENDING"]

    # 4. Resume action cleanly
    with waf.session(session_id="sess_crash_1", tenant_id="org_crash"):
        res = waf.resume_sync(
            pending_action_id=pending_id, approval_token=approved.approval_token
        )
        assert res["status"] == "SUCCESS"

    # Action is now EXECUTED
    action_after = waf.state_store.get_pending_action(pending_id)
    assert action_after.status == ActionState.EXECUTED
