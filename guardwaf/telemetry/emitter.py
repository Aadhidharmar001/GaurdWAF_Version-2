"""
Asynchronous Telemetry Emitter for GuardWAF Events.
Buffers events in memory or sends them to external subscribers without adding latency to tool execution.
"""

import threading
import queue
from typing import List, Callable, Optional
from guardwaf.telemetry.events import TelemetryEvent

class TelemetryEmitter:
    def __init__(self):
        self._listeners: List[Callable[[TelemetryEvent], None]] = []
        self._events_history: List[TelemetryEvent] = []
        self._lock = threading.Lock()

    def add_listener(self, listener: Callable[[TelemetryEvent], None]) -> None:
        with self._lock:
            self._listeners.append(listener)

    def emit(self, event: TelemetryEvent) -> None:
        with self._lock:
            self._events_history.append(event)
            # Retain last 1000 events in memory
            if len(self._events_history) > 1000:
                self._events_history = self._events_history[-1000:]
            
            listeners_copy = list(self._listeners)

        # Notify listeners
        for listener in listeners_copy:
            try:
                listener(event)
            except Exception:
                pass

    def get_recent_events(self, limit: int = 100) -> List[TelemetryEvent]:
        with self._lock:
            return list(reversed(self._events_history[-limit:]))
