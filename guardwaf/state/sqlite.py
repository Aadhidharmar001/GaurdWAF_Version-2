"""
SQLite Persistent Implementation of StateStore.
Provides durable, file-backed state persistence for local development and single-node deployments.
"""

import json
import sqlite3
import threading
from datetime import datetime, timedelta, timezone
from typing import List, Optional

from guardwaf.core.models import ActionState, PendingAction
from guardwaf.state.base import StateStore


class SQLiteStateStore(StateStore):
    def __init__(self, db_path: str = "guardwaf_state.db"):
        self.db_path = db_path
        self._lock = threading.Lock()
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, timeout=10.0)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._lock:
            conn = self._get_connection()
            try:
                cursor = conn.cursor()
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS tool_calls (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        session_id TEXT NOT NULL,
                        tool_name TEXT NOT NULL,
                        timestamp TEXT NOT NULL,
                        status TEXT NOT NULL
                    )
                """)
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS sequence_state (
                        session_id TEXT NOT NULL,
                        tool_name TEXT NOT NULL,
                        PRIMARY KEY (session_id, tool_name)
                    )
                """)
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS pending_actions (
                        pending_action_id TEXT PRIMARY KEY,
                        agent_id TEXT NOT NULL,
                        delegating_principal TEXT,
                        session_id TEXT NOT NULL,
                        tool_name TEXT NOT NULL,
                        canonical_parameters TEXT NOT NULL,
                        parameters_json TEXT NOT NULL,
                        parameter_digest TEXT NOT NULL,
                        action_intent_digest TEXT NOT NULL,
                        policy_decision TEXT NOT NULL,
                        matched_rule TEXT,
                        created_at TEXT NOT NULL,
                        expires_at TEXT NOT NULL,
                        status TEXT NOT NULL,
                        approver_id TEXT,
                        approved_at TEXT,
                        denied_reason TEXT,
                        execution_status TEXT NOT NULL,
                        idempotency_key TEXT NOT NULL,
                        approval_token TEXT
                    )
                """)
                conn.commit()
            finally:
                conn.close()

    def record_tool_call(
        self, session_id: str, tool_name: str, status: str = "allowed"
    ) -> None:
        if status not in ["allowed", "shadow_blocked"]:
            return
        with self._lock:
            conn = self._get_connection()
            try:
                now_str = datetime.now(timezone.utc).isoformat()
                conn.execute(
                    "INSERT INTO tool_calls (session_id, tool_name, timestamp, status) VALUES (?, ?, ?, ?)",
                    (session_id, tool_name, now_str, status),
                )
                conn.commit()
            finally:
                conn.close()

    def get_tool_call_count(
        self, session_id: str, tool_name: str, window_seconds: int
    ) -> int:
        with self._lock:
            conn = self._get_connection()
            try:
                cutoff = (
                    datetime.now(timezone.utc) - timedelta(seconds=window_seconds)
                ).isoformat()
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT COUNT(*) FROM tool_calls WHERE session_id = ? AND tool_name = ? AND timestamp >= ?",
                    (session_id, tool_name, cutoff),
                )
                row = cursor.fetchone()
                return row[0] if row else 0
            finally:
                conn.close()

    def has_executed_predecessor(self, session_id: str, predecessor_tool: str) -> bool:
        with self._lock:
            conn = self._get_connection()
            try:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT 1 FROM sequence_state WHERE session_id = ? AND tool_name = ?",
                    (session_id, predecessor_tool),
                )
                return cursor.fetchone() is not None
            finally:
                conn.close()

    def record_sequence_state(self, session_id: str, tool_name: str) -> None:
        with self._lock:
            conn = self._get_connection()
            try:
                conn.execute(
                    "INSERT OR IGNORE INTO sequence_state (session_id, tool_name) VALUES (?, ?)",
                    (session_id, tool_name),
                )
                conn.commit()
            finally:
                conn.close()

    def clear_session(self, session_id: str) -> None:
        with self._lock:
            conn = self._get_connection()
            try:
                conn.execute(
                    "DELETE FROM tool_calls WHERE session_id = ?", (session_id,)
                )
                conn.execute(
                    "DELETE FROM sequence_state WHERE session_id = ?", (session_id,)
                )
                conn.commit()
            finally:
                conn.close()

    # --- PendingAction SQLite Methods ---

    def save_pending_action(self, pending_action: PendingAction) -> None:
        with self._lock:
            conn = self._get_connection()
            try:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO pending_actions (
                        pending_action_id, agent_id, delegating_principal, session_id, tool_name,
                        canonical_parameters, parameters_json, parameter_digest, action_intent_digest,
                        policy_decision, matched_rule, created_at, expires_at, status,
                        approver_id, approved_at, denied_reason, execution_status, idempotency_key, approval_token
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        pending_action.pending_action_id,
                        pending_action.agent_id,
                        pending_action.delegating_principal,
                        pending_action.session_id,
                        pending_action.tool_name,
                        pending_action.canonical_parameters,
                        json.dumps(pending_action.parameters),
                        pending_action.parameter_digest,
                        pending_action.action_intent_digest,
                        pending_action.policy_decision,
                        pending_action.matched_rule,
                        pending_action.created_at.isoformat(),
                        pending_action.expires_at.isoformat(),
                        pending_action.status.value,
                        pending_action.approver_id,
                        pending_action.approved_at.isoformat()
                        if pending_action.approved_at
                        else None,
                        pending_action.denied_reason,
                        pending_action.execution_status,
                        pending_action.idempotency_key,
                        pending_action.approval_token,
                    ),
                )
                conn.commit()
            finally:
                conn.close()

    def _row_to_pending_action(self, row: sqlite3.Row) -> PendingAction:
        created_at = datetime.fromisoformat(row["created_at"])
        expires_at = datetime.fromisoformat(row["expires_at"])
        approved_at = (
            datetime.fromisoformat(row["approved_at"]) if row["approved_at"] else None
        )

        status_val = ActionState(row["status"])
        now = datetime.now(timezone.utc)
        if status_val == ActionState.PENDING and now > expires_at:
            status_val = ActionState.EXPIRED

        return PendingAction(
            pending_action_id=row["pending_action_id"],
            agent_id=row["agent_id"],
            delegating_principal=row["delegating_principal"],
            session_id=row["session_id"],
            tool_name=row["tool_name"],
            canonical_parameters=row["canonical_parameters"],
            parameters=json.loads(row["parameters_json"]),
            parameter_digest=row["parameter_digest"],
            action_intent_digest=row["action_intent_digest"],
            policy_decision=row["policy_decision"],
            matched_rule=row["matched_rule"],
            created_at=created_at,
            expires_at=expires_at,
            status=status_val,
            approver_id=row["approver_id"],
            approved_at=approved_at,
            denied_reason=row["denied_reason"],
            execution_status=row["execution_status"],
            idempotency_key=row["idempotency_key"],
            approval_token=row["approval_token"],
        )

    def get_pending_action(self, pending_action_id: str) -> Optional[PendingAction]:
        with self._lock:
            conn = self._get_connection()
            try:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT * FROM pending_actions WHERE pending_action_id = ?",
                    (pending_action_id,),
                )
                row = cursor.fetchone()
                if not row:
                    return None
                return self._row_to_pending_action(row)
            finally:
                conn.close()

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
            conn = self._get_connection()
            try:
                conn.execute("BEGIN IMMEDIATE")
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT * FROM pending_actions WHERE pending_action_id = ?",
                    (pending_action_id,),
                )
                row = cursor.fetchone()
                if not row:
                    conn.rollback()
                    return False

                action = self._row_to_pending_action(row)
                if action.status != expected_old_status:
                    conn.rollback()
                    return False

                now_iso = datetime.now(timezone.utc).isoformat()
                exec_status = action.execution_status
                if new_status == ActionState.EXECUTED:
                    exec_status = "EXECUTED"
                elif new_status == ActionState.EXECUTING:
                    exec_status = "EXECUTING"

                appr_time = (
                    now_iso
                    if approver_id
                    else (
                        action.approved_at.isoformat() if action.approved_at else None
                    )
                )

                cursor.execute(
                    """
                    UPDATE pending_actions SET
                        status = ?,
                        approver_id = COALESCE(?, approver_id),
                        approved_at = COALESCE(?, approved_at),
                        denied_reason = COALESCE(?, denied_reason),
                        approval_token = COALESCE(?, approval_token),
                        execution_status = ?
                    WHERE pending_action_id = ? AND status = ?
                """,
                    (
                        new_status.value,
                        approver_id,
                        appr_time,
                        denied_reason,
                        approval_token,
                        exec_status,
                        pending_action_id,
                        expected_old_status.value,
                    ),
                )
                conn.commit()
                return cursor.rowcount > 0
            finally:
                conn.close()

    def list_pending_actions(
        self, status: Optional[ActionState] = None
    ) -> List[PendingAction]:
        with self._lock:
            conn = self._get_connection()
            try:
                cursor = conn.cursor()
                if status:
                    cursor.execute(
                        "SELECT * FROM pending_actions WHERE status = ?",
                        (status.value,),
                    )
                else:
                    cursor.execute("SELECT * FROM pending_actions")
                rows = cursor.fetchall()
                return [self._row_to_pending_action(r) for r in rows]
            finally:
                conn.close()
