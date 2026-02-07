"""Celery task for background ingestion."""

import logging

from src.worker import celery_app
from src.services.ingestion.ingest import run_ingestion

logger = logging.getLogger(__name__)


@celery_app.task(name="ingest_workspace", bind=True, max_retries=1)
def ingest_workspace_task(self, team_id: str, channel_ids: list[str] | None = None) -> dict:
    """Run ingestion for a workspace in the background.

    Args:
        team_id: Slack team ID to ingest.
        channel_ids: Specific channel IDs to ingest. If None, all bot channels.

    Returns:
        Dict with status info.
    """
    logger.info("Starting background ingestion for team %s (%s channels)",
                team_id, len(channel_ids) if channel_ids else "all")
    try:
        run_ingestion(team_id, channel_ids=channel_ids)
        return {"status": "completed", "team_id": team_id}
    except Exception as exc:
        logger.exception("Ingestion task failed for team %s", team_id)
        raise self.retry(exc=exc, countdown=60)
