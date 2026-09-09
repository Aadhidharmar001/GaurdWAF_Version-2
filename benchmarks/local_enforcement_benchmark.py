"""
Workstream C — Local Enforcement Benchmark Tool.
Measures p50, p95, p99 latency and throughput (requests/sec) over 10,000 protected tool calls.
"""

import sys
import time

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from guardwaf import GuardWAF, protect
from guardwaf.core.models import BulkThresholdRule, PolicyConfig, PolicyRules


@protect(tool_name="benchmark_tool")
def benchmark_tool(x: int):
    return x * 2


def run_local_benchmark(total_calls: int = 10000):
    rules = PolicyRules(bulk_thresholds=[BulkThresholdRule(tool="benchmark_tool", param_name="x", max_value=1000000)])
    policy = PolicyConfig(metadata={"policy_name": "bench_policy"}, rules=rules)
    waf = GuardWAF(policy=policy, secret_key="secret_bench_key")
    waf.register_tool("benchmark_tool", benchmark_tool)

    latencies_ms = []
    start_total = time.perf_counter()

    with waf.session(session_id="sess_bench", tenant_id="org_bench"):
        for i in range(total_calls):
            t0 = time.perf_counter()
            res = benchmark_tool(i)
            t1 = time.perf_counter()
            latencies_ms.append((t1 - t0) * 1000.0)

    total_time_sec = time.perf_counter() - start_total
    rps = total_calls / total_time_sec

    latencies_ms.sort()
    p50 = latencies_ms[int(total_calls * 0.50)]
    p95 = latencies_ms[int(total_calls * 0.95)]
    p99 = latencies_ms[int(total_calls * 0.99)]
    max_lat = latencies_ms[-1]

    report = {
        "total_calls": total_calls,
        "total_time_sec": round(total_time_sec, 3),
        "throughput_rps": round(rps, 2),
        "p50_latency_ms": round(p50, 4),
        "p95_latency_ms": round(p95, 4),
        "p99_latency_ms": round(p99, 4),
        "max_latency_ms": round(max_lat, 4),
    }

    print("=" * 65)
    print("🚀 GUARdWAF LOCAL ENFORCEMENT BENCHMARK RESULTS")
    print("=" * 65)
    print(f" Total Requests:      {report['total_calls']:,}")
    print(f" Total Time:          {report['total_time_sec']} sec")
    print(f" Throughput:          {report['throughput_rps']:,} req/sec")
    print(f" p50 Latency:         {report['p50_latency_ms']} ms")
    print(f" p95 Latency:         {report['p95_latency_ms']} ms")
    print(f" p99 Latency:         {report['p99_latency_ms']} ms")
    print(f" Max Latency:         {report['max_latency_ms']} ms")
    print("=" * 65)
    return report


if __name__ == "__main__":
    run_local_benchmark()
