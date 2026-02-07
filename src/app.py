import logging

import uvicorn
from slack_bolt import App
from slack_bolt.authorization import AuthorizeResult

from src.config import settings
from src.services.db.connection import get_db
from src.services.db.workspaces import get_workspace_by_team_id
from src.utils.logger import setup_logging

setup_logging()
logger = logging.getLogger(__name__)


def authorize(enterprise_id, team_id, logger):
    """Look up bot token from our DB for each incoming Slack request."""
    with get_db() as db:
        ws = get_workspace_by_team_id(db, team_id)
        if ws is None:
            raise Exception(f"No workspace found for team {team_id}")
        return AuthorizeResult(
            enterprise_id=enterprise_id,
            team_id=team_id,
            bot_token=ws.bot_token,
        )


app = App(
    authorize=authorize,
    signing_secret=settings.slack_signing_secret,
)

# -- Register handlers --

from src.handlers.events import message as message_handler
from src.handlers.events import uninstall as uninstall_handler
from src.handlers.commands import rule as rule_handler
from src.handlers.commands import stats as stats_handler
from src.handlers.commands import help as help_handler
from src.handlers.actions import review_request as review_request_handler
from src.handlers.actions import feedback as feedback_handler
from src.handlers.actions import onboarding as onboarding_handler
from src.handlers.views import edit_answer as edit_answer_handler
from src.handlers.views import onboarding as onboarding_view_handler

message_handler.register(app)
uninstall_handler.register(app)
rule_handler.register(app)
stats_handler.register(app)
help_handler.register(app)
review_request_handler.register(app)
feedback_handler.register(app)
onboarding_handler.register(app)
edit_answer_handler.register(app)
onboarding_view_handler.register(app)


# -- Entry point --

def main():
    from src.web import create_web_app

    web_app = create_web_app(app)

    if settings.environment == "development" and settings.slack_app_token:
        # Local dev: Socket Mode (no public URL needed)
        from slack_bolt.adapter.socket_mode import SocketModeHandler

        logger.info("Starting Slough.ai bot (Socket Mode — dev)")
        socket_handler = SocketModeHandler(app, settings.slack_app_token)
        socket_handler.connect()
    else:
        # Production: HTTP mode (Slack POSTs to /slack/events)
        logger.info("Starting Slough.ai bot (HTTP Mode — prod)")

    logger.info("Starting FastAPI on port %d", settings.app_port)
    uvicorn.run(web_app, host="0.0.0.0", port=settings.app_port)


if __name__ == "__main__":
    main()
