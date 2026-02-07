"""Block Kit message builders for Slough.ai Slack bot."""

import json

DISCLAIMER = "⚠️ AI가 생성한 응답이며, 오류가 있을 수 있습니다."
HIGH_RISK_WARNING = "⚠️ [주의] 이 주제는 민감하므로, 직접 확인하시는 것을 권장합니다."

MAX_BLOCK_TEXT = 2900  # Stay under Slack's 3000 char limit with margin


def _split_text(text: str) -> list[str]:
    """Split text into chunks that fit in a single Slack section block."""
    if len(text) <= MAX_BLOCK_TEXT:
        return [text]

    chunks = []
    remaining = text
    while remaining:
        if len(remaining) <= MAX_BLOCK_TEXT:
            chunks.append(remaining)
            break
        # Try to split on double newline (paragraph)
        cut = remaining.rfind("\n\n", 0, MAX_BLOCK_TEXT)
        if cut == -1:
            # Try single newline
            cut = remaining.rfind("\n", 0, MAX_BLOCK_TEXT)
        if cut == -1:
            # Try space
            cut = remaining.rfind(" ", 0, MAX_BLOCK_TEXT)
        if cut == -1:
            # Hard cut
            cut = MAX_BLOCK_TEXT
        chunks.append(remaining[:cut])
        remaining = remaining[cut:].lstrip("\n")
    return chunks


def _text_sections(text: str) -> list[dict]:
    """Return one or more section blocks for a long text."""
    return [
        {"type": "section", "text": {"type": "mrkdwn", "text": chunk}}
        for chunk in _split_text(text)
    ]


def build_answer_blocks(
    answer: str,
    is_high_risk: bool,
    qa_id: str,
    message_ts: str,
) -> list[dict]:
    """Build Block Kit blocks for an AI answer sent to the employee.

    Includes: answer text, disclaimer, optional high-risk warning, review request button.
    """
    blocks = []

    # Answer text (chunked for Slack's 3000 char limit)
    blocks.extend(_text_sections(answer))

    # High-risk warning (if applicable)
    if is_high_risk:
        blocks.append({
            "type": "context",
            "elements": [{"type": "mrkdwn", "text": HIGH_RISK_WARNING}],
        })

    # Disclaimer
    blocks.append({
        "type": "context",
        "elements": [{"type": "mrkdwn", "text": DISCLAIMER}],
    })

    blocks.append({"type": "divider"})

    # Review request button
    button_value = json.dumps({"qa_id": qa_id, "message_ts": message_ts})
    blocks.append({
        "type": "actions",
        "elements": [
            {
                "type": "button",
                "text": {"type": "plain_text", "text": "🔍 검토 요청"},
                "action_id": "request_review",
                "value": button_value,
            }
        ],
    })

    return blocks


def build_review_request_blocks(
    asker_id: str,
    question: str,
    answer: str,
    qa_id: str,
) -> list[dict]:
    """Build Block Kit blocks for the review request sent to the decision-maker.

    Shows the question, AI answer, and 4 feedback buttons.
    """
    blocks = [
        {
            "type": "header",
            "text": {"type": "plain_text", "text": "🔍 검토 요청이 도착했습니다"},
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*질문자:* <@{asker_id}>\n*질문:* {question}",
            },
        },
        *_text_sections(f"*AI 응답:*\n{answer}"),
        {"type": "divider"},
        {
            "type": "actions",
            "elements": [
                {
                    "type": "button",
                    "text": {"type": "plain_text", "text": "✅ 문제 없음"},
                    "action_id": "feedback_approved",
                    "style": "primary",
                    "value": json.dumps({
                        "qa_id": qa_id,
                        "asker_id": asker_id,
                    }),
                },
                {
                    "type": "button",
                    "text": {"type": "plain_text", "text": "❌ 틀림"},
                    "action_id": "feedback_rejected",
                    "style": "danger",
                    "value": json.dumps({
                        "qa_id": qa_id,
                        "asker_id": asker_id,
                    }),
                },
                {
                    "type": "button",
                    "text": {"type": "plain_text", "text": "✏️ 직접 수정"},
                    "action_id": "feedback_edit",
                    "value": json.dumps({
                        "qa_id": qa_id,
                        "asker_id": asker_id,
                        "answer": answer,
                    }),
                },
                {
                    "type": "button",
                    "text": {"type": "plain_text", "text": "⚠️ 판단 시 주의 필요"},
                    "action_id": "feedback_caution",
                    "value": json.dumps({
                        "qa_id": qa_id,
                        "asker_id": asker_id,
                    }),
                },
            ],
        },
    ]
    return blocks


def build_feedback_notification(
    feedback_type: str,
    corrected_answer: str | None = None,
) -> list[dict]:
    """Build Block Kit blocks for the feedback notification sent to the employee."""
    messages = {
        "approved": "✅ 확인이 완료되었습니다.",
        "rejected": "❌ 해당 답변이 틀렸다고 판단되었습니다. 직접 문의해 주세요.",
        "corrected": "✅ 내용을 수정하여 전달했습니다.",
        "caution": "⚠️ 이 답변은 신중하게 판단하라는 의견입니다.",
    }

    text = messages.get(feedback_type, "피드백이 처리되었습니다.")

    blocks = [
        {
            "type": "section",
            "text": {"type": "mrkdwn", "text": text},
        },
    ]

    if feedback_type == "corrected" and corrected_answer:
        blocks.extend(_text_sections(f"*수정된 답변:*\n{corrected_answer}"))

    return blocks
