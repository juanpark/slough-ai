import logging

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
from src.handlers.actions import review_request as review_request_handler
from src.handlers.actions import feedback as feedback_handler
from src.handlers.views import edit_answer as edit_answer_handler

message_handler.register(app)
rule_handler.register(app)
review_request_handler.register(app)
feedback_handler.register(app)
edit_answer_handler.register(app)


# -- Entry point --

def main():
    logger.info("Starting Slough.ai bot (Socket Mode)")
    handler = SocketModeHandler(app, settings.slack_app_token)
    handler.start()


if __name__ == "__main__":
    main()
