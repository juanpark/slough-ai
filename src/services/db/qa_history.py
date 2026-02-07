"""QA History CRUD operations."""

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from src.services.db.models import QAHistory


def create_qa_record(
    db: Session,
    *,
    workspace_id: uuid.UUID,
    asker_user_id: str,
    question: str,
    answer: str,
    asker_user_name: str | None = None,
    message_ts: str | None = None,
    channel_id: str | None = None,
    is_high_risk: bool = False,
    matched_rule_id: int | None = None,
) -> QAHistory:
    """Insert a new Q&A record and return it."""
    record = QAHistory(
        id=uuid.uuid4(),
        workspace_id=workspace_id,
        asker_user_id=asker_user_id,
        asker_user_name=asker_user_name,
        question=question,
        answer=answer,
        message_ts=message_ts,
        channel_id=channel_id,
        is_high_risk=is_high_risk,
        matched_rule_id=matched_rule_id,
    )
    db.add(record)
    db.flush()
    return record


def get_qa_record(db: Session, qa_id: uuid.UUID) -> Optional[QAHistory]:
    """Fetch a single QA record by its UUID."""
    return db.query(QAHistory).filter(QAHistory.id == qa_id).first()


def update_review_status(db: Session, qa_id: uuid.UUID, status: str) -> None:
    """Set review_status and review_requested_at timestamp."""
    record = db.query(QAHistory).filter(QAHistory.id == qa_id).first()
    if record is None:
        return
    record.review_status = status
    if status == "requested":
        record.review_requested_at = datetime.utcnow()
    db.flush()


def update_feedback(
    db: Session,
    qa_id: uuid.UUID,
    feedback_type: str,
    corrected_answer: str | None = None,
) -> None:
    """Record decision-maker feedback on a QA record."""
    record = db.query(QAHistory).filter(QAHistory.id == qa_id).first()
    if record is None:
        return
    record.feedback_type = feedback_type
    record.feedback_at = datetime.utcnow()
    record.review_status = "completed"
    if corrected_answer is not None:
        record.corrected_answer = corrected_answer
    db.flush()
