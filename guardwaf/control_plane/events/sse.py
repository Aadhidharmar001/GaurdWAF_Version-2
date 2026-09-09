"""
Server-Sent Events (SSE) Broadcaster with Tenant Filtering and Parameter Redaction.
Telemetry streaming is strictly fault-isolated from local runtime enforcement.
"""

import asyncio
import json
from collections.abc import AsyncGenerator
from typing import Any, Dict, Set

from guardwaf.observability.events import (
    redact_sensitive_parameters,
)


class SSEBroadcaster:
    def __init__(self):
        self._subscribers: Dict[str, Set[asyncio.Queue]] = {}

    def subscribe(self, tenant_id: str) -> asyncio.Queue:
        """Subscribes an async client queue to tenant SSE events."""
        if tenant_id not in self._subscribers:
            self._subscribers[tenant_id] = set()
        queue: asyncio.Queue = asyncio.Queue(maxsize=100)
        self._subscribers[tenant_id].add(queue)
        return queue

    def unsubscribe(self, tenant_id: str, queue: asyncio.Queue) -> None:
        """Unsubscribes a client queue."""
        if tenant_id in self._subscribers:
            self._subscribers[tenant_id].discard(queue)
            if not self._subscribers[tenant_id]:
                del self._subscribers[tenant_id]

    async def broadcast_event(self, tenant_id: str, event_data: Dict[str, Any]) -> None:
        """
        Broadcasting event to connected subscribers for tenant_id.
        Fault isolated: Exceptions in subscribers will not raise to caller.
        """
        if tenant_id not in self._subscribers:
            return

        # Redact sensitive parameters
        if "parameters" in event_data and isinstance(event_data["parameters"], dict):
            event_data["parameters"] = redact_sensitive_parameters(event_data["parameters"])

        dead_queues = set()
        for q in list(self._subscribers[tenant_id]):
            try:
                q.put_nowait(event_data)
            except asyncio.QueueFull:
                dead_queues.add(q)
            except Exception:
                dead_queues.add(q)

        for dq in dead_queues:
            self.unsubscribe(tenant_id, dq)

    async def sse_event_generator(self, tenant_id: str) -> AsyncGenerator[str, None]:
        """Async generator formatting SSE streams for FastAPI EventSourceResponse."""
        queue = self.subscribe(tenant_id)
        try:
            # Yield initial connection message
            yield f"data: {json.dumps({'event_type': 'CONNECTED', 'tenant_id': tenant_id})}\n\n"
            while True:
                data = await queue.get()
                yield f"data: {json.dumps(data)}\n\n"
        except asyncio.CancelledError:
            pass
        finally:
            self.unsubscribe(tenant_id, queue)
