import time
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.config import settings
from app.db.database import get_db

router = APIRouter(tags=["Health Check"])

START_TIME = time.time()


@router.get("/health/live")
def liveness_check():
    return {
        "status": "alive",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "uptime_seconds": int(time.time() - START_TIME),
    }


@router.get("/health/ready")
def readiness_check(db: Session = Depends(get_db)):
    db_status = "ok"
    try:
        db.execute(text("SELECT 1"))
    except Exception as e:
        db_status = f"unhealthy: {e!s}"
        raise HTTPException(status_code=503, detail=f"Database connection error: {db_status}")

    return {
        "status": "ready" if db_status == "ok" else "unhealthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "database": db_status,
        "redis": "ok",
    }


@router.get("/health")
def health_check(db: Session = Depends(get_db)):
    # 1. DB Connectivity Check
    db_status = "ok"
    try:
        db.execute(text("SELECT 1"))
    except Exception as e:
        db_status = f"unhealthy: {e!s}"
        raise HTTPException(status_code=503, detail=f"Database connection error: {db_status}")

    # 2. Compute Uptime
    uptime_seconds = int(time.time() - START_TIME)

    return {
        "status": "healthy" if db_status == "ok" else "degraded",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "uptime_seconds": uptime_seconds,
        "database": {
            "status": db_status,
            "engine": settings.DATABASE_URL.split("://")[0],
        },
        "rule_engine": {
            "status": "loaded",
            "policy_file": settings.RULES_PATH,
            "shadow_mode_global": settings.SHADOW_MODE_GLOBAL,
        },
    }
