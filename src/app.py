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

# -- Event handlers --

@app.event("message")
def handle_message(event, say):
    """Handle DM messages from employees."""
    # TODO: Wire to AI pipeline
    logger.info("Received message", extra={"user": event.get("user"), "channel": event.get("channel")})
    say("[STUB] 메시지를 수신했습니다. AI 파이프라인 연결 전입니다.")


# -- Slash commands --

@app.command("/rule")
def handle_rule_command(ack, command, say):
    """Handle /rule add|list|delete commands."""
    ack()
    # TODO: Implement rule management
    say("[STUB] /rule 명령어를 수신했습니다.")


# -- Entry point --

def main():
    logger.info("Starting Slough.ai bot (Socket Mode)")
    handler = SocketModeHandler(app, settings.slack_app_token)
    handler.start()


if __name__ == "__main__":
    main()
