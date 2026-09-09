"""
Redis Implementation of StateStore for Distributed Runtime Deployments.
Provides atomic rate-limit counters, sequence state, and distributed pending action locks.
"""

from datetime import datetime, timezone
from typing import List, Optional

from guardwaf.core.models import ActionState, PendingAction
from guardwaf.state.base import StateStore

try:
    import redis

    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    redis = None


class RedisStateStore(StateStore):
    def __init__(self, redis_url: str = "redis://localhost:6379/0", client=None):
        if not REDIS_AVAILABLE and client is None:
            # We provide a contract-compatible fallback mock if redis library is not installed
            self._client = None
        else:
            self._client = client or redis.Redis.from_url(redis_url, decode_responses=True)

    def is_available(self) -> bool:
        return self._client is not None

    def record_tool_call(self, session_id: str, tool_name: str, status: str = "allowed") -> None:
        if status not in ["allowed", "shadow_blocked"]:
            return
        if not self._client:
            return
        key = f"gw:rate:{session_id}:{tool_name}"
        now_ts = datetime.now(timezone.utc).timestamp()
        pipe = self._client.pipeline()
        pipe.zadd(key, {str(now_ts): now_ts})
        pipe.expire(key, 3600)
        pipe.execute()

    def get_tool_call_count(self, session_id: str, tool_name: str, window_seconds: int) -> int:
        if not self._client:
            return 0
        key = f"gw:rate:{session_id}:{tool_name}"
        now_ts = datetime.now(timezone.utc).timestamp()
        cutoff = now_ts - window_seconds
        pipe = self._client.pipeline()
        pipe.zremrangebyscore(key, "-inf", cutoff)
        pipe.zcard(key)
        results = pipe.execute()
        return results[1] if len(results) > 1 else 0

    def has_executed_predecessor(self, session_id: str, predecessor_tool: str) -> bool:
        if not self._client:
            return False
        key = f"gw:seq:{session_id}"
        return self._client.sismember(key, predecessor_tool)

    def record_sequence_state(self, session_id: str, tool_name: str) -> None:
        if not self._client:
            return
        key = f"gw:seq:{session_id}"
        pipe = self._client.pipeline()
        pipe.sadd(key, tool_name)
        pipe.expire(key, 86400)
        pipe.execute()

    def clear_session(self, session_id: str) -> None:
        if not self._client:
            return
        keys = self._client.keys(f"gw:*:{session_id}*")
        if keys:
            self._client.delete(*keys)

    # --- PendingAction Redis Methods ---

    def save_pending_action(self, pending_action: PendingAction) -> None:
        if not self._client:
            return
        key = f"gw:pending:{pending_action.pending_action_id}"
        data = pending_action.model_dump_json()
        self._client.set(key, data, ex=86400)

    def get_pending_action(self, pending_action_id: str) -> Optional[PendingAction]:
        if not self._client:
            return None
        key = f"gw:pending:{pending_action_id}"
        raw = self._client.get(key)
        if not raw:
            return None
        action = PendingAction.model_validate_json(raw)
        now = datetime.now(timezone.utc)
        if action.status == ActionState.PENDING and now > action.expires_at:
            action.status = ActionState.EXPIRED
        return action

    def update_pending_action_status(
        self,
        pending_action_id: str,
        new_status: ActionState,
        expected_old_status: ActionState,
        approver_id: Optional[str] = None,
        denied_reason: Optional[str] = None,
        approval_token: Optional[str] = None,
    ) -> bool:
        if not self._client:
            return False
        key = f"gw:pending:{pending_action_id}"

        # Redis Watch for optimistic atomic state update
        with self._client.pipeline() as pipe:
            try:
                pipe.watch(key)
                raw = pipe.get(key)
                if not raw:
                    pipe.unwatch()
                    return False
                action = PendingAction.model_validate_json(raw)
                if action.status != expected_old_status:
                    pipe.unwatch()
                    return False

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

                pipe.multi()
                pipe.set(key, action.model_dump_json(), ex=86400)
                pipe.execute()
                return True
            except Exception:
                return False

    def list_pending_actions(self, status: Optional[ActionState] = None) -> List[PendingAction]:
        if not self._client:
            return []
        keys = self._client.keys("gw:pending:*")
        results = []
        for key in keys:
            raw = self._client.get(key)
            if raw:
                act = PendingAction.model_validate_json(raw)
                if status is None or act.status == status:
                    results.append(act)
        return results
