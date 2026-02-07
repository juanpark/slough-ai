"""Ingestion job CRUD operations."""

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from src.services.db.models import IngestionJob


def create_ingestion_job(db: Session, *, workspace_id: uuid.UUID) -> IngestionJob:
    """Create a new ingestion job in 'pending' status."""
    job = IngestionJob(
        id=uuid.uuid4(),
        workspace_id=workspace_id,
        status="pending",
    )
    db.add(job)
    db.flush()
    return job


def update_ingestion_job(db: Session, job_id: uuid.UUID, **fields) -> Optional[IngestionJob]:
    """Update ingestion job fields."""
    job = db.query(IngestionJob).filter(IngestionJob.id == job_id).first()
    if job is None:
        return None
    for key, value in fields.items():
        if hasattr(job, key):
            setattr(job, key, value)
    db.flush()
    return job


def mark_job_running(db: Session, job_id: uuid.UUID, total_channels: int) -> Optional[IngestionJob]:
    """Mark a job as running with the total channel count."""
    return update_ingestion_job(
        db, job_id,
        status="running",
        total_channels=total_channels,
        started_at=datetime.utcnow(),
    )


def mark_job_completed(
    db: Session,
    job_id: uuid.UUID,
    total_messages: int,
    processed_messages: int,
) -> Optional[IngestionJob]:
    """Mark a job as completed."""
    return update_ingestion_job(
        db, job_id,
        status="completed",
        total_messages=total_messages,
        processed_messages=processed_messages,
        completed_at=datetime.utcnow(),
    )


def mark_job_failed(db: Session, job_id: uuid.UUID, error: str) -> Optional[IngestionJob]:
    """Mark a job as failed with an error message."""
    return update_ingestion_job(
        db, job_id,
        status="failed",
        error_message=error,
        completed_at=datetime.utcnow(),
    )


def get_latest_job(db: Session, workspace_id: uuid.UUID) -> Optional[IngestionJob]:
    """Get the most recent ingestion job for a workspace."""
    return (
        db.query(IngestionJob)
        .filter(IngestionJob.workspace_id == workspace_id)
        .order_by(IngestionJob.created_at.desc())
        .first()
    )
