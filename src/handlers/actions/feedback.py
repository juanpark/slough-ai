"""Handlers for decision-maker feedback buttons (approved, rejected, edit, caution)."""

import asyncio
import json
import logging

from src.services.ai import process_feedback
from src.utils.blocks import build_feedback_notification

logger = logging.getLogger(__name__)


def register(app):
    """Register all feedback action handlers."""

    @app.action("feedback_approved")
    def handle_approved(ack, body, client):
        ack()
        _handle_feedback(body, client, "approved")

    @app.action("feedback_rejected")
    def handle_rejected(ack, body, client):
        ack()
        _handle_feedback(body, client, "rejected")

    @app.action("feedback_caution")
    def handle_caution(ack, body, client):
        ack()
        _handle_feedback(body, client, "caution")

    @app.action("feedback_edit")
    def handle_edit(ack, body, client):
        ack()
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
    workspace_id = body.get("team", {}).get("id", "stub-workspace")

    # Call AI feedback stub
    asyncio.run(
        process_feedback(
            workspace_id=workspace_id,
            question_id=qa_id,
            feedback_type=feedback_type,
        )
    )

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
    current_answer = payload.get("answer", "")

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
