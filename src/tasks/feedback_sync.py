"""Celery Beat tasks — feedback sync and rules cache sync.

Feedback sync: every 5 minutes, find unreflected corrected Q&A feedback
and embed it into the knowledge base.

Rules sync: daily at midnight, sync active rules from DB → Redis cache.
"""

import logging

from src.worker import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="sync_feedback_to_kb")
def sync_feedback_to_kb():
    """Batch-process unreflected corrected feedback into the KB.

    Queries qa_history for records with review_status='corrected' that
    haven't been reflected yet, embeds them, and stores in pgvector.
    """
    from src.services.db import get_db
    from src.services.db.models import QAHistory
    from src.services.ai.vector_store import store_embeddings
    from sqlalchemy import select

    success = 0
    failed = 0

    try:
        with get_db() as db:
            # Find corrected but unreflected feedback
            records = db.execute(
                select(QAHistory).where(
                    QAHistory.review_status == "corrected",
                    QAHistory.is_reflected == False,  # noqa: E712
                )
            ).scalars().all()

            if not records:
                return {"success": 0, "failed": 0, "message": "No pending feedback"}

            logger.info("Processing %d unreflected feedback records", len(records))

            for record in records:
                try:
                    # Build Q&A content for embedding
                    content = f"질문: {record.question}\n\n정답: {record.corrected_answer or record.answer}"

                    chunk = {
                        "content": content,
                        "channel_id": record.channel_id or "",
                        "message_ts": str(record.id),
                        "thread_ts": None,
                    }

                    store_embeddings(str(record.workspace_id), [chunk])

                    # Mark as reflected
                    record.is_reflected = True
                    success += 1

                except Exception:
                    logger.exception(
                        "Failed to process feedback for QA %s", record.id
                    )
                    failed += 1

            db.commit()

    except Exception:
        logger.exception("Feedback sync task failed")

    logger.info("Feedback sync: %d success, %d failed", success, failed)
    return {"success": success, "failed": failed}


@celery_app.task(name="sync_rules_from_db")
def sync_rules_from_db_task():
    """Sync active rules from PostgreSQL → Redis cache."""
    from src.services.redis_client import sync_rules_from_db

    count = sync_rules_from_db()
    logger.info("Synced %d rules from DB to Redis", count)
    return {"synced_rules": count}
