"""
Abstract Base Class for GuardWAF State Storage.
Supports Rate Limiting, Sequence State, and Durable Pending Action Management.
"""

from abc import ABC, abstractmethod
from typing import List, Optional

from guardwaf.core.models import ActionState, PendingAction


class StateStore(ABC):
    @abstractmethod
    def record_tool_call(self, session_id: str, tool_name: str, status: str = "allowed") -> None:
        """Records an executed tool invocation for rate limiting and sequence tracking."""

    @abstractmethod
    def get_tool_call_count(self, session_id: str, tool_name: str, window_seconds: int) -> int:
        """Returns the number of times a tool was called in a session within window_seconds."""

    @abstractmethod
    def has_executed_predecessor(self, session_id: str, predecessor_tool: str) -> bool:
        """Checks if a predecessor tool was previously executed in the active session."""

    @abstractmethod
    def record_sequence_state(self, session_id: str, tool_name: str) -> None:
        """Records a successful tool execution into the session sequence state."""

    @abstractmethod
    def clear_session(self, session_id: str) -> None:
        """Clears sequence state and counters for a given session."""

    # --- Durable PendingAction Methods ---

    @abstractmethod
    def save_pending_action(self, pending_action: PendingAction) -> None:
        """Saves an immutable PendingAction record."""

    @abstractmethod
    def get_pending_action(self, pending_action_id: str) -> Optional[PendingAction]:
        """Retrieves a PendingAction record by ID."""

    @abstractmethod
    def update_pending_action_status(
        self,
        pending_action_id: str,
        new_status: ActionState,
        expected_old_status: ActionState,
        approver_id: Optional[str] = None,
        denied_reason: Optional[str] = None,
        approval_token: Optional[str] = None,
    ) -> bool:
        """
        Atomically updates the status of a PendingAction if current status matches expected_old_status.
        Returns True if successful, False if state transition failed (e.g. state mismatch).
        """

    @abstractmethod
    def list_pending_actions(self, status: Optional[ActionState] = None) -> List[PendingAction]:
        """Lists PendingAction records, optionally filtered by status."""
