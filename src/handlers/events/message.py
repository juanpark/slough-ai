"""DM message handler — receives employee questions, returns AI answers."""

import asyncio
import logging
import uuid

from src.services.ai import generate_answer
from src.utils.keywords import detect_high_risk_keywords
from src.utils.blocks import build_answer_blocks

logger = logging.getLogger(__name__)

# Prohibited-domain refusal message
PROHIBITED_RESPONSE = (
    "죄송합니다. 이 주제는 법적·재무적·운영상 판단이 필요한 영역으로, "
    "AI가 답변을 제공할 수 없습니다. 직접 의사결정자에게 문의해 주세요."
)


def register(app):
    """Register the message event handler on the Bolt app."""

    @app.event("message")
    def handle_message(event, say, client):
        # Only handle plain DM messages (no subtypes like bot_message, message_changed, etc.)
        if event.get("subtype"):
            return

        # Only handle DMs (channel_type == "im")
        if event.get("channel_type") != "im":
            return

        user_id = event.get("user")
        text = event.get("text", "").strip()
        channel = event.get("channel")
        message_ts = event.get("ts")

        if not text:
            return

        logger.info("DM received", extra={"user": user_id, "channel": channel})

        # Generate answer via AI stub (run async in sync context)
        # TODO: workspace_id and rules will come from DB later
        workspace_id = "stub-workspace"
        rules = []

        result = asyncio.run(
            generate_answer(
                question=text,
                workspace_id=workspace_id,
                asker_id=user_id,
                rules=rules,
            )
        )

        # Handle prohibited domain
        if result.is_prohibited:
            say(text=PROHIBITED_RESPONSE, channel=channel)
            return

        # Check for high-risk keywords in the question
        risk_check = detect_high_risk_keywords(text)
        is_high_risk = result.is_high_risk or risk_check["is_high_risk"]

        # Generate a QA ID (will be a DB ID later)
        qa_id = str(uuid.uuid4())

        # Build and send Block Kit response
        blocks = build_answer_blocks(
            answer=result.answer,
            is_high_risk=is_high_risk,
            qa_id=qa_id,
            message_ts=message_ts,
        )

        say(blocks=blocks, text=result.answer, channel=channel)
