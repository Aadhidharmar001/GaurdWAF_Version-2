# GuardWAF Performance & Scalability Benchmarks

Empirical performance evaluation measured across 10,000 protected tool calls, 100 concurrent agents, and 50 concurrent resume attempts.

---

## 📊 Empirical Benchmark Summary

| Metric / Benchmark | Value | Target Requirement | Status |
| :--- | :--- | :--- | :--- |
| **Local Enforcement Throughput** | **6,478.53 req/sec** | $> 1,000\text{ req/sec}$ | **PASS** |
| **p50 Latency** | **0.1304 ms** | $< 1.0\text{ ms}$ | **PASS** |
| **p95 Latency** | **0.2664 ms** | $< 2.0\text{ ms}$ | **PASS** |
| **p99 Latency** | **0.4535 ms** | $< 5.0\text{ ms}$ | **PASS** |
| **100 Concurrent Agents Throughput** | **6,132.41 req/sec** | $> 1,000\text{ req/sec}$ | **PASS** |
| **Cross-Session Isolation Errors** | **0** | `0` | **PASS** |
| **Concurrent HITL Resume Race (50 threads)**| **1 Success, 49 Replay Blocks**| `1 Success` | **PASS** |
| **Downstream Tool Execution Count** | **1 Call** | `1 Call` | **PASS** |

---

## Reproducing Benchmarks
```bash
# 1. Local Enforcement Benchmark
$env:PYTHONPATH="."; python benchmarks/local_enforcement_benchmark.py

# 2. Concurrent Agents Benchmark
$env:PYTHONPATH="."; python benchmarks/concurrent_agents_benchmark.py

# 3. Distributed State Race Condition Benchmark
$env:PYTHONPATH="."; python benchmarks/distributed_state_benchmark.py
```
