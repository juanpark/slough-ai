"""DM message handler — receives employee questions, returns AI answers."""

import asyncio
import logging

from src.services.ai import generate_answer
from src.services.db import get_db
from src.services.db.workspaces import get_workspace_by_team_id
from src.services.db.rules import get_active_rules
from src.services.db.qa_history import create_qa_record
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
        team_id = event.get("team")

        if not text:
            return

        logger.info("DM received", extra={"user": user_id, "channel": channel})

        # Look up workspace from DB
        with get_db() as db:
            workspace = get_workspace_by_team_id(db, team_id) if team_id else None

            if workspace is None:
                say(text="워크스페이스 설정이 완료되지 않았습니다. 관리자에게 문의해 주세요.", channel=channel)
                return

            workspace_id = workspace.id

            # Fetch active rules for AI context
            active_rules = get_active_rules(db, workspace_id)
            rules = [{"id": r.id, "rule_text": r.rule_text} for r in active_rules]

        # Generate answer via AI stub (run async in sync context)
        result = asyncio.run(
            generate_answer(
                question=text,
                workspace_id=str(workspace_id),
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

        # Persist Q&A record to DB
        with get_db() as db:
            record = create_qa_record(
                db,
                workspace_id=workspace_id,
                asker_user_id=user_id,
                question=text,
                answer=result.answer,
                message_ts=message_ts,
                channel_id=channel,
                is_high_risk=is_high_risk,
            )
            qa_id = str(record.id)

        # Build and send Block Kit response
        blocks = build_answer_blocks(
            answer=result.answer,
            is_high_risk=is_high_risk,
            qa_id=qa_id,
            message_ts=message_ts,
        )

        say(blocks=blocks, text=result.answer, channel=channel)
