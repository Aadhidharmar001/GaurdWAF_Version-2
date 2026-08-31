from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, DateTime, Float, ForeignKey, Index
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    agent_id = Column(String(100), nullable=False, index=True)
    session_id = Column(String(100), nullable=False, index=True)
    tool = Column(String(100), nullable=False, index=True)
    parameters = Column(Text, nullable=False)
    evaluation_outcome = Column(Text, nullable=False)
    matched_rule = Column(String(255), nullable=True)
    status = Column(String(50), nullable=False, index=True)
    latency_ms = Column(Float, nullable=True, default=0.0)

class HitlQueue(Base):
    __tablename__ = "hitl_queue"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    agent_id = Column(String(100), nullable=False)
    session_id = Column(String(100), nullable=False)
    tool = Column(String(100), nullable=False)
    parameters = Column(Text, nullable=False)
    status = Column(String(50), default="pending", index=True) # pending, approved, rejected
    reason = Column(Text, nullable=True)
    fraud_score = Column(Float, nullable=True, default=0.0)
    confidence_score = Column(Float, nullable=True, default=0.0)
    risk_level = Column(String(50), nullable=True, default="MEDIUM")
    risk_reasons = Column(Text, nullable=True)

class SequenceState(Base):
    __tablename__ = "sequence_state"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(100), nullable=False, index=True)
    tool_name = Column(String(100), nullable=False, index=True)
    executed_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("idx_session_tool", "session_id", "tool_name"),
    )
