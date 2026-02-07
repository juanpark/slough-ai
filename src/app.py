import logging

import uvicorn
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

from src.config import settings
from src.utils.logger import setup_logging

setup_logging()
logger = logging.getLogger(__name__)

app = App(
    token=settings.slack_bot_token,
    signing_secret=settings.slack_signing_secret,
)

# -- Register handlers --

from src.handlers.events import message as message_handler
from src.handlers.commands import rule as rule_handler
from src.handlers.commands import stats as stats_handler
from src.handlers.commands import help as help_handler
from src.handlers.actions import review_request as review_request_handler
from src.handlers.actions import feedback as feedback_handler
from src.handlers.actions import onboarding as onboarding_handler
from src.handlers.views import edit_answer as edit_answer_handler
from src.handlers.views import onboarding as onboarding_view_handler

message_handler.register(app)
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
    # Start Socket Mode in a background thread (non-blocking)
    logger.info("Starting Slough.ai bot (Socket Mode)")
    socket_handler = SocketModeHandler(app, settings.slack_app_token)
    socket_handler.connect()

    # Start FastAPI in the main thread (blocking)
    from src.web import web_app

    logger.info("Starting FastAPI on port %d", settings.app_port)
    uvicorn.run(web_app, host="0.0.0.0", port=settings.app_port)


if __name__ == "__main__":
    main()
