"""
Revocation Event Broadcast Transport Abstractions (SSE & Polling Fallback).
"""

from abc import ABC, abstractmethod
from typing import Callable, List

from guardwaf.control_plane.events.events import (
    SignedRevocationEvent,
)


class RevocationTransport(ABC):
    @abstractmethod
    def broadcast_event(self, event: SignedRevocationEvent) -> None:
        pass

    @abstractmethod
    def subscribe(self, callback: Callable[[SignedRevocationEvent], None]) -> None:
        pass


class MemoryRevocationTransport(RevocationTransport):
    def __init__(self):
        self._subscribers: List[Callable[[SignedRevocationEvent], None]] = []

    def broadcast_event(self, event: SignedRevocationEvent) -> None:
        for cb in self._subscribers:
            try:
                cb(event)
            except Exception as e:
                print(f"⚠️ [RevocationTransport] Error dispatching event to subscriber: {e}")

    def subscribe(self, callback: Callable[[SignedRevocationEvent], None]) -> None:
        self._subscribers.append(callback)
