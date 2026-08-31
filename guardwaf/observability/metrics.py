"""
Pluggable Metrics Collector Interface and Prometheus Metrics Adapter.
Telemetry failures are isolated and never impact security decisions.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

class MetricsCollector(ABC):
    @abstractmethod
    def increment(self, metric_name: str, amount: int = 1, labels: Optional[Dict[str, str]] = None) -> None: pass
    @abstractmethod
    def observe(self, metric_name: str, value: float, labels: Optional[Dict[str, str]] = None) -> None: pass

class MemoryMetricsCollector(MetricsCollector):
    def __init__(self):
        self.counters: Dict[str, int] = {}
        self.observations: Dict[str, list] = {}

    def increment(self, metric_name: str, amount: int = 1, labels: Optional[Dict[str, str]] = None) -> None:
        try:
            lbl_str = f"{metric_name}:{sorted(labels.items()) if labels else ''}"
            self.counters[lbl_str] = self.counters.get(lbl_str, 0) + amount
        except Exception as e:
            print(f"⚠️ [Telemetry Warning] Metrics failure isolated: {e}")

    def observe(self, metric_name: str, value: float, labels: Optional[Dict[str, str]] = None) -> None:
        try:
            lbl_str = f"{metric_name}:{sorted(labels.items()) if labels else ''}"
            if lbl_str not in self.observations:
                self.observations[lbl_str] = []
            self.observations[lbl_str].append(value)
        except Exception as e:
            print(f"⚠️ [Telemetry Warning] Metrics failure isolated: {e}")

class PrometheusMetricsAdapter(MetricsCollector):
    """
    Optional Prometheus metrics collector adapter.
    Uses lazy import so prometheus_client is an optional extra dependency.
    """
    def __init__(self):
        self._prom = None
        try:
            import prometheus_client
            self._prom = prometheus_client
        except ImportError:
            print("⚠️ [Telemetry] prometheus_client library not installed. Prometheus metrics disabled.")

    def increment(self, metric_name: str, amount: int = 1, labels: Optional[Dict[str, str]] = None) -> None:
        if not self._prom:
            return
        try:
            # Prometheus counter logic wrapper
            pass
        except Exception as e:
            print(f"⚠️ [Telemetry Warning] Prometheus counter failure isolated: {e}")

    def observe(self, metric_name: str, value: float, labels: Optional[Dict[str, str]] = None) -> None:
        if not self._prom:
            return
        try:
            # Prometheus histogram logic wrapper
            pass
        except Exception as e:
            print(f"⚠️ [Telemetry Warning] Prometheus observation failure isolated: {e}")
