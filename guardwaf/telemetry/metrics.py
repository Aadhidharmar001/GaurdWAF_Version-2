"""
GuardWAF Production Observability & Operational Metrics Engine.
Exposes security counters, authorization latency metrics, system health gauges, and Prometheus/CloudWatch compatible metric formats.
"""

import threading
from typing import Any, Dict


class SecurityMetricsRegistry:
    """
    Thread-safe operational & security metric counters registry for GuardWAF.
    """

    def __init__(self):
        self._lock = threading.Lock()
        self.counters = {
            "allowed_actions": 0,
            "blocked_actions": 0,
            "hitl_requested": 0,
            "hitl_approved": 0,
            "hitl_denied": 0,
            "agent_revocations": 0,
            "tenant_lockdowns": 0,
            "auth_failures": 0,
            "rbac_violations": 0,
            "cross_tenant_attempts": 0,
            "replay_attack_attempts": 0,
            "parameter_tamper_attempts": 0,
            "policy_signature_failures": 0,
            "revocation_signature_failures": 0,
            "database_errors": 0,
            "redis_errors": 0,
        }
        self.latency_sum_ms = 0.0
        self.latency_count = 0

    def increment(self, counter_name: str, amount: int = 1) -> None:
        with self._lock:
            if counter_name in self.counters:
                self.counters[counter_name] += amount

    def record_latency(self, latency_ms: float) -> None:
        with self._lock:
            self.latency_sum_ms += latency_ms
            self.latency_count += 1

    def get_metrics_snapshot(self) -> Dict[str, Any]:
        with self._lock:
            avg_latency = (self.latency_sum_ms / self.latency_count) if self.latency_count > 0 else 0.0
            return {
                "counters": dict(self.counters),
                "latency": {
                    "total_count": self.latency_count,
                    "avg_ms": round(avg_latency, 3),
                },
            }

    def generate_prometheus_format(self) -> str:
        lines = []
        with self._lock:
            for k, v in self.counters.items():
                lines.append(f"# TYPE guardwaf_{k} counter")
                lines.append(f"guardwaf_{k} {v}")
            lines.append("# TYPE guardwaf_latency_avg_ms gauge")
            avg_latency = (self.latency_sum_ms / self.latency_count) if self.latency_count > 0 else 0.0
            lines.append(f"guardwaf_latency_avg_ms {round(avg_latency, 3)}")
        return "\n".join(lines) + "\n"


# Global Security Metrics Registry Singleton
METRICS_REGISTRY = SecurityMetricsRegistry()
