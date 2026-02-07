"""Handler for the '검토 요청' (review request) button click."""

import json
import logging

from src.utils.blocks import build_review_request_blocks

logger = logging.getLogger(__name__)

# TODO: Replace with DB lookup per workspace
STUB_DECISION_MAKER_ID = "DECISION_MAKER_USER_ID"


def register(app):
    """Register the review request action handler."""

    @app.action("request_review")
    def handle_request_review(ack, body, client):
        ack()

        user_id = body["user"]["id"]
        action = body["actions"][0]

        try:
            payload = json.loads(action["value"])
        except (json.JSONDecodeError, KeyError):
            logger.error("Failed to parse review request payload")
            return

        qa_id = payload.get("qa_id", "")

        # Get the original message to extract question and answer
        channel = body["channel"]["id"]
        message = body.get("message", {})
        # The answer is in the first block's text
        answer = ""
        if message.get("blocks"):
            first_block = message["blocks"][0]
            answer = first_block.get("text", {}).get("text", "")

        # Get the original question from the conversation
        # For now, we look at the previous message in the thread
        # TODO: Store question in DB and retrieve by qa_id
        question = "(원본 질문을 불러올 수 없습니다 — DB 연결 후 개선 예정)"

        # Try to get the question from the message before the bot reply
        try:
            history = client.conversations_history(
                channel=channel,
                latest=message.get("ts"),
                limit=2,
                inclusive=False,
            )
            if history["messages"]:
                # Messages are in reverse chronological order
                for msg in history["messages"]:
                    if msg.get("user") == user_id:
                        question = msg.get("text", question)
                        break
        except Exception:
            logger.warning("Could not fetch conversation history for question")

        # Send review request to decision-maker
        blocks = build_review_request_blocks(
            asker_id=user_id,
            question=question,
            answer=answer,
            qa_id=qa_id,
        )

        try:
            # Open DM with decision-maker
            dm = client.conversations_open(users=[STUB_DECISION_MAKER_ID])
            dm_channel = dm["channel"]["id"]

            client.chat_postMessage(
                channel=dm_channel,
                blocks=blocks,
                text=f"검토 요청: {question[:50]}...",
            )
        except Exception:
            logger.exception("Failed to send review request to decision-maker")
            # Notify user of failure
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
