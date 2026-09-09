from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.config import settings
from app.db.orm_models import Base

# Set connect_args for SQLite fallback
connect_args = {}
if settings.DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(settings.DATABASE_URL, connect_args=connect_args, pool_pre_ping=True)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    Base.metadata.create_all(bind=engine)
    # Ensure latency_ms column exists for SQLite/existing tables
    try:
        with engine.connect() as conn:
            conn.execute(text("ALTER TABLE audit_logs ADD COLUMN latency_ms FLOAT DEFAULT 0.0"))
            conn.commit()
    except Exception:
        pass  # Column already exists

    # Ensure HITL score columns exist
    for col_def in [
        ("fraud_score", "FLOAT DEFAULT 0.0"),
        ("confidence_score", "FLOAT DEFAULT 0.0"),
        ("risk_level", "VARCHAR(50) DEFAULT 'MEDIUM'"),
        ("risk_reasons", "TEXT"),
    ]:
        try:
            with engine.connect() as conn:
                conn.execute(text(f"ALTER TABLE hitl_queue ADD COLUMN {col_def[0]} {col_def[1]}"))
                conn.commit()
        except Exception:
            pass  # Column already exists


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
