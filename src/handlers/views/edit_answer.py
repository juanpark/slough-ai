"""Handler for the edit_answer_submit modal view submission."""

import asyncio
import json
import logging
import uuid as uuid_mod

from src.services.ai import process_feedback
from src.services.db import get_db
from src.services.db.qa_history import update_feedback
from src.utils.blocks import build_feedback_notification

logger = logging.getLogger(__name__)


def register(app):
    """Register the edit answer modal submission handler."""

    @app.view("edit_answer_submit")
    def handle_edit_answer_submit(ack, body, client, view):
        ack()

        # Extract corrected answer from modal input
        values = view["state"]["values"]
        corrected_answer = (
            values["corrected_answer_block"]["corrected_answer"]["value"] or ""
        ).strip()

        if not corrected_answer:
            return

        # Parse metadata
        try:
            metadata = json.loads(view.get("private_metadata", "{}"))
        except json.JSONDecodeError:
            logger.error("Failed to parse edit modal metadata")
            return

        qa_id = metadata.get("qa_id", "")
        asker_id = metadata.get("asker_id", "")
        channel_id = metadata.get("channel_id", "")
        message_ts = metadata.get("message_ts", "")
        workspace_id = body.get("team", {}).get("id", "stub-workspace")

        # Persist feedback to DB
        try:
            qa_uuid = uuid_mod.UUID(qa_id)
            with get_db() as db:
                update_feedback(db, qa_uuid, "corrected", corrected_answer)
        except (ValueError, Exception):
            logger.warning("Could not update feedback in DB", extra={"qa_id": qa_id})

        # Call AI feedback pipeline
        try:
            asyncio.run(
                process_feedback(
                    workspace_id=workspace_id,
                    question_id=qa_id,
                    feedback_type="corrected",
                    corrected_answer=corrected_answer,
                )
            )
        except Exception:
            logger.exception("AI process_feedback failed", extra={"qa_id": qa_id})

        # Update the decision-maker's review message to show edit was applied
        if channel_id and message_ts:
            try:
                result = client.conversations_history(
                    channel=channel_id,
                    latest=message_ts,
                    inclusive=True,
                    limit=1,
                )
                original_blocks = []
                if result["messages"]:
                    original_blocks = result["messages"][0].get("blocks", [])

                updated_blocks = [b for b in original_blocks if b["type"] != "actions"]
                updated_blocks.append({
                    "type": "context",
                    "elements": [{"type": "mrkdwn", "text": "*피드백 완료:* ✏️ 직접 수정"}],
                })

                client.chat_update(
                    channel=channel_id,
                    ts=message_ts,
                    blocks=updated_blocks,
                    text="피드백 완료: 직접 수정",
                )
            except Exception:
                logger.exception("Failed to update decision-maker message after edit")

        # Notify the employee with the corrected answer
        if asker_id:
            blocks = build_feedback_notification("corrected", corrected_answer)
            try:
                dm = client.conversations_open(users=[asker_id])
                dm_channel = dm["channel"]["id"]
                client.chat_postMessage(
                    channel=dm_channel,
                    blocks=blocks,
                    text="✅ 내용을 수정하여 전달했습니다.",
                )
            except Exception:
                logger.exception("Failed to notify employee of edit")
