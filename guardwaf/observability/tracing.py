"""
OpenTelemetry Tracing Context and Correlation Propagation.
Guarantees correlation IDs flow through SDK, MCP Gateway, HITL, and Control Plane.
"""

import uuid
from typing import Dict, Optional


class TraceContext:
    def __init__(self, correlation_id: Optional[str] = None):
        self.correlation_id = correlation_id or f"corr_{uuid.uuid4().hex[:10]}"

    def inject_headers(self) -> Dict[str, str]:
        return {"x-guardwaf-correlation-id": self.correlation_id}

    @classmethod
    def extract_headers(cls, headers: Dict[str, str]) -> "TraceContext":
        cid = headers.get("x-guardwaf-correlation-id") or headers.get("X-GuardWAF-Correlation-ID")
        return cls(correlation_id=cid)
