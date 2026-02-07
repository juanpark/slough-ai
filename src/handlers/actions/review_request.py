"""Handler for the '검토 요청' (review request) button click."""

import json
import logging
import uuid as uuid_mod

from src.services.db import get_db
from src.services.db.workspaces import get_workspace_by_team_id
from src.services.db.qa_history import get_qa_record, update_review_status
from src.utils.blocks import build_review_request_blocks

logger = logging.getLogger(__name__)


def register(app):
    """Register the review request action handler."""

    @app.action("request_review")
    def handle_request_review(ack, body, client):
        ack()

        user_id = body["user"]["id"]
        action = body["actions"][0]
        team_id = body.get("team", {}).get("id", "")

        try:
            payload = json.loads(action["value"])
        except (json.JSONDecodeError, KeyError):
            logger.error("Failed to parse review request payload")
            return

        qa_id = payload.get("qa_id", "")
        channel = body["channel"]["id"]

        # Look up workspace for decision_maker_id
        with get_db() as db:
            workspace = get_workspace_by_team_id(db, team_id)
            if workspace is None:
                logger.error("Workspace not found for review request", extra={"team_id": team_id})
                client.chat_postMessage(
                    channel=channel,
                    text="워크스페이스 설정이 완료되지 않았습니다.",
                )
                return
            decision_maker_id = workspace.decision_maker_id

        # Try to get question and answer from the QA record in DB
        question = "(원본 질문을 불러올 수 없습니다)"
        answer = ""
        try:
            qa_uuid = uuid_mod.UUID(qa_id)
            with get_db() as db:
                record = get_qa_record(db, qa_uuid)
                if record:
                    question = record.question
                    answer = record.answer
                    update_review_status(db, qa_uuid, "requested")
        except (ValueError, Exception):
            logger.warning("Could not fetch QA record", extra={"qa_id": qa_id})
            # Fall back to reading from the message
            message = body.get("message", {})
            if message.get("blocks"):
                first_block = message["blocks"][0]
                answer = first_block.get("text", {}).get("text", "")

        # Send review request to decision-maker
        blocks = build_review_request_blocks(
            asker_id=user_id,
            question=question,
            answer=answer,
            qa_id=qa_id,
        )

        try:
            dm = client.conversations_open(users=[decision_maker_id])
            dm_channel = dm["channel"]["id"]

            client.chat_postMessage(
                channel=dm_channel,
                blocks=blocks,
                text=f"검토 요청: {question[:50]}...",
            )
        except Exception:
            logger.exception("Failed to send review request to decision-maker")
            client.chat_postMessage(
                channel=channel,
                text="검토 요청 전송에 실패했습니다. 관리자에게 문의해 주세요.",
            )
            return

        # Notify the employee that review was requested
        client.chat_postMessage(
            channel=channel,
            text="🔍 의사결정자에게 검토 요청이 전달되었습니다. 확인 후 알려드리겠습니다.",
        )
