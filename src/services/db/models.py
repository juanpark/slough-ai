"""ORM models matching scripts/init-db.sql."""

import uuid

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from src.services.db.connection import Base


class Workspace(Base):
    __tablename__ = "workspaces"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    slack_team_id = Column(String(20), unique=True, nullable=False)
    slack_team_name = Column(String(255))
    admin_id = Column(String(20), nullable=False)
    decision_maker_id = Column(String(20), nullable=False)
    bot_token = Column(Text, nullable=False)
    user_token = Column(Text, nullable=True, default="")
    installed_at = Column(DateTime, server_default=func.now())
    uninstalled_at = Column(DateTime, nullable=True)
    data_deletion_at = Column(DateTime, nullable=True)  # 30 days after uninstall
    onboarding_completed = Column(Boolean, default=False)
    onboarding_completed_at = Column(DateTime)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    rules = relationship("Rule", back_populates="workspace", cascade="all, delete-orphan")
    qa_history = relationship("QAHistory", back_populates="workspace", cascade="all, delete-orphan")
    weekly_stats = relationship("WeeklyStat", back_populates="workspace", cascade="all, delete-orphan")
    ingestion_jobs = relationship("IngestionJob", back_populates="workspace", cascade="all, delete-orphan")


class Rule(Base):
    __tablename__ = "rules"

    id = Column(Integer, primary_key=True, autoincrement=True)
    workspace_id = Column(UUID(as_uuid=True), ForeignKey("workspaces.id", ondelete="CASCADE"))
    rule_text = Column(Text, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    workspace = relationship("Workspace", back_populates="rules")


class QAHistory(Base):
    __tablename__ = "qa_history"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workspace_id = Column(UUID(as_uuid=True), ForeignKey("workspaces.id", ondelete="CASCADE"))
    asker_user_id = Column(String(20), nullable=False)
    asker_user_name = Column(String(255))
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    message_ts = Column(String(20))
    channel_id = Column(String(20))

    # Review tracking
    review_status = Column(String(20), default="none")
    review_requested_at = Column(DateTime)

    # Decision-maker feedback
    feedback_type = Column(String(20))
    corrected_answer = Column(Text)
    feedback_at = Column(DateTime)

    # Metadata
    is_high_risk = Column(Boolean, default=False)
    matched_rule_id = Column(Integer, ForeignKey("rules.id"))

    created_at = Column(DateTime, server_default=func.now())

    workspace = relationship("Workspace", back_populates="qa_history")
    matched_rule = relationship("Rule")


class WeeklyStat(Base):
    __tablename__ = "weekly_stats"

    id = Column(Integer, primary_key=True, autoincrement=True)
    workspace_id = Column(UUID(as_uuid=True), ForeignKey("workspaces.id", ondelete="CASCADE"))
    week_start = Column(Date, nullable=False)
    week_end = Column(Date, nullable=False)
    total_questions = Column(Integer, default=0)
    review_requests = Column(Integer, default=0)
    feedback_completed = Column(Integer, default=0)
    feedback_approved = Column(Integer, default=0)
    feedback_rejected = Column(Integer, default=0)
    feedback_corrected = Column(Integer, default=0)
    feedback_caution = Column(Integer, default=0)
    created_at = Column(DateTime, server_default=func.now())

    workspace = relationship("Workspace", back_populates="weekly_stats")

    __table_args__ = (
        UniqueConstraint("workspace_id", "week_start"),
    )


class IngestionJob(Base):
    __tablename__ = "ingestion_jobs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workspace_id = Column(UUID(as_uuid=True), ForeignKey("workspaces.id", ondelete="CASCADE"))
    status = Column(String(20), default="pending")
    total_channels = Column(Integer, default=0)
    processed_channels = Column(Integer, default=0)
    total_messages = Column(Integer, default=0)
    processed_messages = Column(Integer, default=0)
    error_message = Column(Text)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    created_at = Column(DateTime, server_default=func.now())

    workspace = relationship("Workspace", back_populates="ingestion_jobs")
