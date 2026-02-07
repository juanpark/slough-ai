"""Weekly stats CRUD and aggregation queries."""

import uuid
from datetime import date, datetime, timedelta

from sqlalchemy import func
from sqlalchemy.orm import Session

from src.services.db.models import QAHistory, WeeklyStat


def get_period_stats(db: Session, workspace_id: uuid.UUID, start: date, end: date) -> dict:
    """Aggregate QA stats for a workspace within a date range.

    Returns a dict with all the stat fields.
    """
    # Convert dates to datetimes for comparison
    start_dt = datetime.combine(start, datetime.min.time())
    end_dt = datetime.combine(end, datetime.max.time())

    base = (
        db.query(QAHistory)
        .filter(
            QAHistory.workspace_id == workspace_id,
            QAHistory.created_at >= start_dt,
            QAHistory.created_at <= end_dt,
        )
    )

    total_questions = base.count()

    review_requests = base.filter(
        QAHistory.review_status.in_(["requested", "completed"])
    ).count()

    feedback_completed = base.filter(QAHistory.feedback_type.isnot(None)).count()

    feedback_approved = base.filter(QAHistory.feedback_type == "approved").count()
    feedback_rejected = base.filter(QAHistory.feedback_type == "rejected").count()
    feedback_corrected = base.filter(QAHistory.feedback_type == "corrected").count()
    feedback_caution = base.filter(QAHistory.feedback_type == "caution").count()

    return {
        "total_questions": total_questions,
        "review_requests": review_requests,
        "feedback_completed": feedback_completed,
        "feedback_approved": feedback_approved,
        "feedback_rejected": feedback_rejected,
        "feedback_corrected": feedback_corrected,
        "feedback_caution": feedback_caution,
    }


def save_weekly_stat(
    db: Session, workspace_id: uuid.UUID, week_start: date, week_end: date, stats: dict
) -> WeeklyStat:
    """Save or update a weekly stat row."""
    existing = (
        db.query(WeeklyStat)
        .filter(
            WeeklyStat.workspace_id == workspace_id,
            WeeklyStat.week_start == week_start,
        )
        .first()
    )

    if existing:
        for key, value in stats.items():
            if hasattr(existing, key):
                setattr(existing, key, value)
        db.flush()
        return existing

    row = WeeklyStat(
        workspace_id=workspace_id,
        week_start=week_start,
        week_end=week_end,
        **stats,
    )
    db.add(row)
    db.flush()
    return row


def get_current_week_range() -> tuple[date, date]:
    """Get Monday-to-Sunday range for the current week."""
    today = date.today()
    monday = today - timedelta(days=today.weekday())
    sunday = monday + timedelta(days=6)
    return monday, sunday


def get_last_week_range() -> tuple[date, date]:
    """Get Monday-to-Sunday range for last week."""
    today = date.today()
    last_monday = today - timedelta(days=today.weekday() + 7)
    last_sunday = last_monday + timedelta(days=6)
    return last_monday, last_sunday
