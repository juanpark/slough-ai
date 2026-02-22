"""Handlers for decision-maker feedback buttons (approved, rejected, edit, caution)."""

import asyncio
import json
import logging
import uuid as uuid_mod

from src.services.ai import process_feedback
from src.services.db import get_db
from src.services.db.workspaces import get_workspace_by_team_id
from src.services.db.qa_history import get_qa_record, update_feedback
from src.utils.blocks import build_feedback_notification

logger = logging.getLogger(__name__)


def _check_is_decision_maker(body, client) -> bool:
    """Verify the user clicking is the decision-maker. Returns False and notifies if not."""
    user_id = body["user"]["id"]
    team_id = body.get("team", {}).get("id")

    if not team_id:
        return True  # Can't verify, allow

    try:
        with get_db() as db:
            workspace = get_workspace_by_team_id(db, team_id)
            if workspace and workspace.decision_maker_id != user_id:
                client.chat_postEphemeral(
                    channel=body["channel"]["id"],
                    user=user_id,
                    text="피드백은 의사결정자만 제출할 수 있습니다.",
                )
                return False
    except Exception:
        logger.exception("Failed to check decision-maker permission")

    return True


def register(app):
    """Register all feedback action handlers."""

    @app.action("feedback_approved")
    def handle_approved(ack, body, client):
        ack()
        if _check_is_decision_maker(body, client):
            _handle_feedback(body, client, "approved")

    @app.action("feedback_rejected")
    def handle_rejected(ack, body, client):
        ack()
        if _check_is_decision_maker(body, client):
            _handle_feedback(body, client, "rejected")

    @app.action("feedback_caution")
    def handle_caution(ack, body, client):
        ack()
        if _check_is_decision_maker(body, client):
            _handle_feedback(body, client, "caution")

    @app.action("feedback_edit")
    def handle_edit(ack, body, client):
        ack()
        if _check_is_decision_maker(body, client):
            _open_edit_modal(body, client)


def _handle_feedback(body: dict, client, feedback_type: str):
    """Process a simple feedback action (approved/rejected/caution)."""
    action = body["actions"][0]

    try:
        payload = json.loads(action["value"])
    except (json.JSONDecodeError, KeyError):
        logger.error("Failed to parse feedback payload")
        return

    qa_id = payload.get("qa_id", "")
    asker_id = payload.get("asker_id", "")
    team_id = body.get("team", {}).get("id", "")

    # Persist feedback to DB
    try:
        qa_uuid = uuid_mod.UUID(qa_id)
        with get_db() as db:
            update_feedback(db, qa_uuid, feedback_type)
    except (ValueError, Exception):
        logger.warning("Could not update feedback in DB", extra={"qa_id": qa_id})

    # Call AI feedback pipeline
    try:
        asyncio.run(
            process_feedback(
                workspace_id=team_id,
                question_id=qa_id,
                feedback_type=feedback_type,
            )
        )
    except Exception:
        logger.exception("AI process_feedback failed", extra={"qa_id": qa_id})

    # Update the decision-maker's message to show feedback was given
    channel = body["channel"]["id"]
    message_ts = body["message"]["ts"]

    try:
        feedback_labels = {
            "approved": "✅ 문제 없음",
            "rejected": "❌ 틀림",
            "caution": "⚠️ 판단 시 주의 필요",
        }
        label = feedback_labels.get(feedback_type, feedback_type)

        # Replace buttons with confirmation text
        original_blocks = body["message"].get("blocks", [])
        updated_blocks = [b for b in original_blocks if b["type"] != "actions"]
        updated_blocks.append({
            "type": "context",
            "elements": [{"type": "mrkdwn", "text": f"*피드백 완료:* {label}"}],
        })

        client.chat_update(
            channel=channel,
            ts=message_ts,
            blocks=updated_blocks,
            text=f"피드백 완료: {label}",
        )
    except Exception:
        logger.exception("Failed to update decision-maker message")

    # Notify the employee
    if asker_id:
        _notify_employee(client, asker_id, feedback_type)


def _open_edit_modal(body: dict, client):
    """Open a modal for the decision-maker to edit the answer."""
    action = body["actions"][0]
    trigger_id = body["trigger_id"]

    try:
        payload = json.loads(action["value"])
    except (json.JSONDecodeError, KeyError):
        logger.error("Failed to parse edit payload")
        return

    qa_id = payload.get("qa_id", "")
    asker_id = payload.get("asker_id", "")

    # Fetch current answer from DB (not from button value — Slack 2000 char limit)
    current_answer = ""
    try:
        qa_uuid = uuid_mod.UUID(qa_id)
        with get_db() as db:
            record = get_qa_record(db, qa_uuid)
            if record:
                current_answer = record.answer
    except Exception:
        logger.warning("Could not fetch answer for edit modal", extra={"qa_id": qa_id})

    # Store context in private_metadata so we can access it on submission
    private_metadata = json.dumps({
        "qa_id": qa_id,
        "asker_id": asker_id,
        "channel_id": body["channel"]["id"],
        "message_ts": body["message"]["ts"],
    })

    try:
        client.views_open(
            trigger_id=trigger_id,
            view={
                "type": "modal",
                "callback_id": "edit_answer_submit",
                "title": {"type": "plain_text", "text": "답변 수정"},
                "submit": {"type": "plain_text", "text": "수정 완료"},
                "close": {"type": "plain_text", "text": "취소"},
                "private_metadata": private_metadata,
                "blocks": [
                    {
                        "type": "input",
                        "block_id": "corrected_answer_block",
                        "element": {
                            "type": "plain_text_input",
                            "action_id": "corrected_answer",
                            "multiline": True,
                            "initial_value": current_answer,
                        },
                        "label": {"type": "plain_text", "text": "수정된 답변"},
                    }
                ],
            },
        )
    except Exception:
        logger.exception("Failed to open edit modal")


def _notify_employee(client, asker_id: str, feedback_type: str, corrected_answer: str | None = None):
    """Send a feedback notification DM to the employee."""
    blocks = build_feedback_notification(feedback_type, corrected_answer)

    try:
        dm = client.conversations_open(users=[asker_id])
        dm_channel = dm["channel"]["id"]
        client.chat_postMessage(
            channel=dm_channel,
            blocks=blocks,
            text=blocks[0]["text"]["text"],
        )
    except Exception:
        logger.exception("Failed to notify employee", extra={"asker_id": asker_id})
