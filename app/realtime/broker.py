from __future__ import annotations

import asyncio
import json
from collections.abc import AsyncGenerator
from datetime import datetime, timezone

from app.db.database import SessionLocal
from app.db.orm_models import AuditLog, HitlQueue


async def stream_dashboard_events(
    poll_interval: float = 2.0,
) -> AsyncGenerator[str, None]:
    while True:

        def fetch_metrics():
            db = SessionLocal()
            try:
                latest_log = db.query(AuditLog).order_by(AuditLog.id.desc()).first()
                pending_hitl = (
                    db.query(HitlQueue).filter(HitlQueue.status == "pending").count()
                )
                total_logs = db.query(AuditLog).count()
                blocked_logs = (
                    db.query(AuditLog).filter(AuditLog.status == "blocked").count()
                )
                return {
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "latest_log_id": latest_log.id if latest_log else 0,
                    "stats": {
                        "total": total_logs,
                        "blocked": blocked_logs,
                        "pending_hitl": pending_hitl,
                    },
                }
            finally:
                db.close()

        payload = await asyncio.to_thread(fetch_metrics)
        yield f"event: dashboard\ndata: {json.dumps(payload)}\n\n"
        await asyncio.sleep(poll_interval)
