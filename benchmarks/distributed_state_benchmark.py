"""
Workstream C — Distributed State Race Condition Benchmark.
Simulates concurrent resume attempts for the exact same PendingAction to verify exactly-once execution.
"""

import concurrent.futures
import sys
import time

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from guardwaf import GuardWAF, GuardWAFHITLRequiredError, GuardWAFSecurityError, protect
from guardwaf.core.models import HITLRule, PolicyConfig, PolicyRules

RESUME_EXEC_COUNT = 0


@protect(tool_name="race_tool")
def race_tool(amount: float):
    global RESUME_EXEC_COUNT
    RESUME_EXEC_COUNT += 1
    return {"status": "EXECUTED", "amount": amount}


def attempt_resume_worker(waf: GuardWAF, pending_id: str, token: str):
    try:
        res = waf.resume_sync(pending_action_id=pending_id, approval_token=token)
        return True, "SUCCESS"
    except Exception as e:
        return False, str(e)


def run_distributed_state_benchmark(num_concurrent_threads: int = 50):
    global RESUME_EXEC_COUNT
    RESUME_EXEC_COUNT = 0

    rules = PolicyRules(hitl_rules=[HITLRule(tool="race_tool", condition_param="amount", greater_than=10.0)])
    policy = PolicyConfig(metadata={"policy_name": "race_policy"}, rules=rules)
    waf = GuardWAF(policy=policy, secret_key="secret_race_key")
    waf.register_tool("race_tool", race_tool)

    # 1. Trigger PendingAction
    pending_id = None
    with waf.session(session_id="sess_race", tenant_id="org_race"):
        try:
            race_tool(100.0)
        except (GuardWAFHITLRequiredError, GuardWAFSecurityError) as e:
            pending_id = getattr(e, "pending_action_id", None)
            if not pending_id:
                pending_id = waf.state_store.list_pending_actions()[-1].pending_action_id

    # 2. Approve PendingAction
    approved = waf.approve_pending_action(pending_id, approver_id="admin_approver")
    token = approved.approval_token

    # 3. Fire concurrent resume attempts across 50 threads simultaneously
    start_t = time.perf_counter()
    with concurrent.futures.ThreadPoolExecutor(max_workers=num_concurrent_threads) as executor:
        futures = [executor.submit(attempt_resume_worker, waf, pending_id, token) for _ in range(num_concurrent_threads)]
        results = [f.result() for f in concurrent.futures.as_completed(futures)]

    total_time_sec = time.perf_counter() - start_t
    successes = sum(1 for ok, _ in results if ok)
    failures = sum(1 for ok, _ in results if not ok)

    report = {
        "num_concurrent_resume_attempts": num_concurrent_threads,
        "successful_resumes": successes,
        "blocked_replay_attempts": failures,
        "downstream_execution_count": RESUME_EXEC_COUNT,
        "total_time_sec": round(total_time_sec, 3),
    }

    print("=" * 65)
    print("🚀 GUARdWAF DISTRIBUTED STATE RACE CONDITION BENCHMARK RESULTS")
    print("=" * 65)
    print(f" Concurrent Resume Attempts: {report['num_concurrent_resume_attempts']}")
    print(f" Successful Resumes:        {report['successful_resumes']}")
    print(f" Blocked Replay Attempts:   {report['blocked_replay_attempts']}")
    print(f" Downstream Tool Calls:     {report['downstream_execution_count']}")
    print("=" * 65)

    # CRITICAL EXACTLY-ONCE INVARIANT VERIFICATION
    assert report["successful_resumes"] == 1
    assert report["downstream_execution_count"] == 1
    assert report["blocked_replay_attempts"] == num_concurrent_threads - 1
    return report


if __name__ == "__main__":
    run_distributed_state_benchmark()
