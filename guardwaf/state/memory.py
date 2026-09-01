"""
In-Memory Thread-Safe State Store with Sliding-Window Rate Limit Counters, Sequence State, and Durable Pending Actions.
"""

import threading
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Set, Tuple

from guardwaf.core.models import ActionState, PendingAction
from guardwaf.state.base import StateStore


class MemoryStateStore(StateStore):
    def __init__(self):
        self._lock = threading.Lock()
        # session_id -> list of (tool_name, timestamp)
        self._call_history: Dict[str, List[Tuple[str, datetime]]] = {}
        # session_id -> set of executed tool_names
        self._sequence_history: Dict[str, Set[str]] = {}
        # pending_action_id -> PendingAction
        self._pending_actions: Dict[str, PendingAction] = {}

    def record_tool_call(
        self, session_id: str, tool_name: str, status: str = "allowed"
    ) -> None:
        with self._lock:
            now = datetime.now(timezone.utc)
            if session_id not in self._call_history:
                self._call_history[session_id] = []
            if status in ["allowed", "shadow_blocked"]:
                self._call_history[session_id].append((tool_name, now))

    def get_tool_call_count(
        self, session_id: str, tool_name: str, window_seconds: int
    ) -> int:
        with self._lock:
            if session_id not in self._call_history:
                return 0
            cutoff = datetime.now(timezone.utc) - timedelta(seconds=window_seconds)
            matching = [
                ts
                for tool, ts in self._call_history[session_id]
                if tool == tool_name and ts >= cutoff
            ]
            return len(matching)

    def has_executed_predecessor(self, session_id: str, predecessor_tool: str) -> bool:
        with self._lock:
            if session_id not in self._sequence_history:
                return False
            return predecessor_tool in self._sequence_history[session_id]

    def record_sequence_state(self, session_id: str, tool_name: str) -> None:
        with self._lock:
            if session_id not in self._sequence_history:
                self._sequence_history[session_id] = set()
            self._sequence_history[session_id].add(tool_name)

    def clear_session(self, session_id: str) -> None:
        with self._lock:
            self._call_history.pop(session_id, None)
            self._sequence_history.pop(session_id, None)

    # --- PendingAction Methods ---

    def save_pending_action(self, pending_action: PendingAction) -> None:
        with self._lock:
            self._pending_actions[pending_action.pending_action_id] = (
                pending_action.model_copy()
            )

    def get_pending_action(self, pending_action_id: str) -> Optional[PendingAction]:
        with self._lock:
            action = self._pending_actions.get(pending_action_id)
            if not action:
                return None

            # Check expiration
            if (
                action.status == ActionState.PENDING
                and datetime.now(timezone.utc) > action.expires_at
            ):
                action.status = ActionState.EXPIRED

            return action.model_copy()

    def update_pending_action_status(
        self,
        pending_action_id: str,
        new_status: ActionState,
        expected_old_status: ActionState,
        approver_id: Optional[str] = None,
        denied_reason: Optional[str] = None,
        approval_token: Optional[str] = None,
    ) -> bool:
        with self._lock:
            action = self._pending_actions.get(pending_action_id)
            if not action:
                return False

            # Check expiration before transition
            if (
                action.status == ActionState.PENDING
                and datetime.now(timezone.utc) > action.expires_at
            ):
                action.status = ActionState.EXPIRED
                return False

            # Verify current status matches expected_old_status
            if action.status != expected_old_status:
                return False

            # Update status atomically
            action.status = new_status
            if approver_id:
                action.approver_id = approver_id
                action.approved_at = datetime.now(timezone.utc)
            if denied_reason:
                action.denied_reason = denied_reason
            if approval_token:
                action.approval_token = approval_token
            if new_status == ActionState.EXECUTED:
                action.execution_status = "EXECUTED"
            elif new_status == ActionState.EXECUTING:
                action.execution_status = "EXECUTING"

            self._pending_actions[pending_action_id] = action
            return True

    def list_pending_actions(
        self, status: Optional[ActionState] = None
    ) -> List[PendingAction]:
        with self._lock:
            now = datetime.now(timezone.utc)
            results = []
            for action in self._pending_actions.values():
                act_copy = action.model_copy()
                if act_copy.status == ActionState.PENDING and now > act_copy.expires_at:
                    act_copy.status = ActionState.EXPIRED
                if status is None or act_copy.status == status:
                    results.append(act_copy)
            return results
