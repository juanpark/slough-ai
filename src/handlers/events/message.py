"""DM message handler — receives employee questions, returns AI answers."""

import asyncio
import logging
import time

from src.services.ai import generate_answer_streaming
from src.services.db import get_db
from src.services.db.workspaces import get_workspace_by_team_id
from src.services.db.rules import get_active_rules
from src.services.db.qa_history import create_qa_record
from src.services.redis_client import is_duplicate_event
from src.utils.keywords import detect_high_risk_keywords
from src.utils.prohibited import check_prohibited
from src.utils.blocks import build_answer_blocks

logger = logging.getLogger(__name__)

PROHIBITED_RESPONSE = (
    "죄송합니다. 이 주제는 법적·재무적·운영상 판단이 필요한 영역으로, "
    "AI가 답변을 제공할 수 없습니다. 직접 의사결정자에게 문의해 주세요."
)

FALLBACK_RESPONSE = (
    "죄송합니다. 일시적인 오류가 발생했습니다. 잠시 후 다시 시도해 주세요."
)



def register(app):
    """Register message and app_mention event handlers."""

    @app.event("app_mention")
    def handle_app_mention(event, say, client):
        """Handle mentions in channels (e.g. @SloughAI 질문)."""
        # Always reply in thread for mentions
        thread_ts = event.get("thread_ts") or event.get("ts")
        _process_question(event, say, client, thread_ts=thread_ts)

    @app.event("message")
    def handle_dm(event, say, client):
        """Handle direct messages (no mention needed)."""
        # Ignore bot messages and message subtypes
        if event.get("subtype") or event.get("bot_id"):
            return

        # Only handle DMs here
        if event.get("channel_type") != "im":
            return

        # For DMs, reply in thread if user replied in thread, else main channel
        thread_ts = event.get("thread_ts")
        _process_question(event, say, client, thread_ts=thread_ts)


def _process_question(event, say, client, thread_ts=None):
    """Common logic for processing questions via RAG (Dedup, Rules, AI, DB)."""
    # ── Dedup check ──
    event_id = event.get("client_msg_id") or event.get("ts")
    if event_id and is_duplicate_event(event_id):
        logger.debug("Duplicate event ignored: %s", event_id)
        return

    user_id = event.get("user")
    text = event.get("text", "").strip()
    channel = event.get("channel")
    message_ts = event.get("ts")
    team_id = event.get("team")

    # Remove mention (<@U12345>) from text if present
    # (Slack sends "<@U12345> 질문 내용")
    if text and "<@" in text:
        import re
        text = re.sub(r"<@[A-Z0-9]+>", "", text).strip()

    if not text:
        return

    logger.info("Processing question", extra={"user": user_id, "channel": channel})

    # Look up workspace
    try:
        with get_db() as db:
            workspace = get_workspace_by_team_id(db, team_id) if team_id else None

            if workspace is None:
                say(
                    text="워크스페이스 설정이 완료되지 않았습니다. 관리자에게 문의해 주세요.",
                    channel=channel,
                    thread_ts=thread_ts,
                )
                return

            workspace_id = workspace.id
            active_rules = get_active_rules(db, workspace_id)
            rules = [{"id": r.id, "rule_text": r.rule_text} for r in active_rules]
    except Exception:
        logger.exception("DB error during workspace/rules lookup")
        say(text=FALLBACK_RESPONSE, channel=channel, thread_ts=thread_ts)
        return

    # Check prohibited content locally
    prohibited_check = check_prohibited(text)
    if prohibited_check["is_prohibited"]:
        logger.info(
            "Prohibited domain detected",
            extra={"matched": prohibited_check["matched"]},
        )
        say(text=PROHIBITED_RESPONSE, channel=channel, thread_ts=thread_ts)
        return

    # ── Send streaming indicator ──
    indicator_ts = None
    try:
        indicator_msg = client.chat_postMessage(
            channel=channel,
            text="💭 답변 생성 중...",
            thread_ts=thread_ts,
        )
        indicator_ts = indicator_msg["ts"]
    except Exception:
        logger.exception("Failed to send streaming indicator")

    # Streaming callback — updates Slack message with partial answer
    _last_update: dict = {"t": 0.0}

    def _on_streaming_chunk(text_so_far: str):
        now = time.time()
        if now - _last_update["t"] < 2.5:  # throttle: max 1 update / 2.5s
            return
        _last_update["t"] = now
        if not indicator_ts:
            return
        try:
            client.chat_update(
                channel=channel,
                ts=indicator_ts,
                text=text_so_far + " ▌",
            )
        except Exception:
            pass

    # ── Generate answer via AI (streaming) ──
    try:
        result = asyncio.run(
            generate_answer_streaming(
                question=text,
                workspace_id=str(workspace_id),
                asker_id=user_id,
                rules=rules,
                on_chunk=_on_streaming_chunk,
            )
        )
    except Exception:
        logger.exception("AI generate_answer failed")
        if indicator_ts:
            try:
                client.chat_update(
                    channel=channel, ts=indicator_ts, text=FALLBACK_RESPONSE,
                )
            except Exception:
                say(text=FALLBACK_RESPONSE, channel=channel, thread_ts=thread_ts)
        else:
            say(text=FALLBACK_RESPONSE, channel=channel, thread_ts=thread_ts)
        return

    if result.is_prohibited:
        if indicator_ts:
            try:
                client.chat_update(
                    channel=channel, ts=indicator_ts, text=PROHIBITED_RESPONSE,
                )
            except Exception:
                say(text=PROHIBITED_RESPONSE, channel=channel, thread_ts=thread_ts)
        else:
            say(text=PROHIBITED_RESPONSE, channel=channel, thread_ts=thread_ts)
        return

    risk_check = detect_high_risk_keywords(text)
    is_high_risk = result.is_high_risk or risk_check["is_high_risk"]

    # Persist
    qa_id = ""
    try:
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
    except Exception:
        logger.exception("Failed to persist QA record")

    # ── Final update — replace indicator with complete answer + buttons ──
    blocks = build_answer_blocks(
        answer=result.answer,
        is_high_risk=is_high_risk,
        qa_id=qa_id,
        message_ts=message_ts,
    )

    if indicator_ts:
        try:
            client.chat_update(
                channel=channel,
                ts=indicator_ts,
                blocks=blocks,
                text=result.answer,
            )
        except Exception:
            logger.exception("Failed to update streaming message with final answer")
            try:
                client.chat_update(
                    channel=channel, ts=indicator_ts, text=result.answer,
                )
            except Exception:
                pass
    else:
        try:
            say(blocks=blocks, text=result.answer, channel=channel, thread_ts=thread_ts)
        except Exception:
            logger.exception("Failed to send response")
            try:
                say(text=result.answer, channel=channel, thread_ts=thread_ts)
            except Exception:
                pass
