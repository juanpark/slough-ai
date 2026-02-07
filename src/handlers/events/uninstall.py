"""Handler for app_uninstalled event — marks workspace inactive."""

import logging
from datetime import datetime, timedelta, timezone

from src.services.db.connection import get_db
from src.services.db.workspaces import get_workspace_by_team_id, update_workspace

logger = logging.getLogger(__name__)

DATA_RETENTION_DAYS = 30


def register(app):
    """Register the app_uninstalled event handler."""

    @app.event("app_uninstalled")
    def handle_app_uninstalled(event, context):
        team_id = context.get("team_id", "")
        logger.info("App uninstalled for team %s", team_id)

        if not team_id:
            return

        now = datetime.now(timezone.utc)
        deletion_date = now + timedelta(days=DATA_RETENTION_DAYS)

        try:
            with get_db() as db:
                workspace = get_workspace_by_team_id(db, team_id)
                if workspace is None:
                    logger.warning("Workspace not found for uninstall event: %s", team_id)
                    return

                update_workspace(
                    db,
                    workspace.id,
                    bot_token="REVOKED",
                    user_token="",
                    uninstalled_at=now,
                    data_deletion_at=deletion_date,
                )

            logger.info(
                "Workspace %s marked as uninstalled. Data deletion scheduled for %s",
                team_id,
                deletion_date.strftime("%Y-%m-%d"),
            )
        except Exception:
            logger.exception("Failed to handle app_uninstalled for team %s", team_id)
