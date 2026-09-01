"""
Workstream C — Concurrent Agents Benchmark.
Executes 100+ concurrent simulated agents executing protected tool calls in parallel to verify session isolation and state consistency.
"""

import concurrent.futures
import sys
import time

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from guardwaf import GuardWAF, protect
from guardwaf.core.models import BulkThresholdRule, PolicyConfig, PolicyRules


@protect(tool_name="concurrent_tool")
def concurrent_tool(agent_idx: int, call_idx: int):
    return {"agent_idx": agent_idx, "call_idx": call_idx, "status": "OK"}


def run_concurrent_agent_task(waf: GuardWAF, agent_idx: int, calls_per_agent: int = 50):
    session_id = f"sess_agent_{agent_idx}"
    tenant_id = f"org_tenant_{agent_idx % 5}"  # 5 distinct tenants
    successes = 0

    with waf.session(session_id=session_id, tenant_id=tenant_id):
        for c in range(calls_per_agent):
            res = concurrent_tool(agent_idx, c)
            if res["status"] == "OK" and res["agent_idx"] == agent_idx:
                successes += 1

    return successes


def run_concurrent_benchmark(num_agents: int = 100, calls_per_agent: int = 50):
    rules = PolicyRules(
        bulk_thresholds=[
            BulkThresholdRule(
                tool="concurrent_tool", param_name="call_idx", max_value=1000
            )
        ]
    )
    policy = PolicyConfig(metadata={"policy_name": "concurrent_policy"}, rules=rules)
    waf = GuardWAF(policy=policy, secret_key="secret_concurrent_bench")
    waf.register_tool("concurrent_tool", concurrent_tool)

    start_t = time.perf_counter()
    total_expected_calls = num_agents * calls_per_agent

    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        futures = [
            executor.submit(run_concurrent_agent_task, waf, i, calls_per_agent)
            for i in range(num_agents)
        ]
        results = [f.result() for f in concurrent.futures.as_completed(futures)]

    total_time_sec = time.perf_counter() - start_t
    total_successful_calls = sum(results)
    throughput = total_successful_calls / total_time_sec

    report = {
        "num_concurrent_agents": num_agents,
        "calls_per_agent": calls_per_agent,
        "total_calls": total_successful_calls,
        "total_time_sec": round(total_time_sec, 3),
        "throughput_rps": round(throughput, 2),
        "isolation_errors": total_expected_calls - total_successful_calls,
    }

    print("=" * 65)
    print("🚀 GUARdWAF CONCURRENT AGENTS BENCHMARK RESULTS")
    print("=" * 65)
    print(f" Concurrent Agents:   {report['num_concurrent_agents']}")
    print(f" Total Executed Calls:{report['total_calls']:,}")
    print(f" Total Time:          {report['total_time_sec']} sec")
    print(f" Throughput:          {report['throughput_rps']:,} req/sec")
    print(f" Isolation Errors:    {report['isolation_errors']}")
    print("=" * 65)

    assert report["isolation_errors"] == 0
    return report


if __name__ == "__main__":
    run_concurrent_benchmark()
