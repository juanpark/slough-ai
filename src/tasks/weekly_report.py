"""Celery task for the weekly report — runs every Monday at 10:00 AM KST."""

import logging

from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

from src.worker import celery_app
from src.services.db.connection import get_db
from src.services.db.models import Workspace
from src.services.db.weekly_stats import (
    get_last_week_range,
    get_period_stats,
    save_weekly_stat,
)

logger = logging.getLogger(__name__)


@celery_app.task(name="send_weekly_reports")
def send_weekly_reports() -> dict:
    """Send weekly report DMs to all decision-makers."""
    week_start, week_end = get_last_week_range()
    sent = 0
    failed = 0

    with get_db() as db:
        workspaces = db.query(Workspace).filter(Workspace.onboarding_completed.is_(True)).all()

        for ws in workspaces:
            try:
                stats = get_period_stats(db, ws.id, week_start, week_end)
                save_weekly_stat(db, ws.id, week_start, week_end, stats)

                _send_report_dm(ws.bot_token, ws.decision_maker_id, stats, week_start, week_end)
                sent += 1
            except Exception:
                logger.exception("Failed to send weekly report for team %s", ws.slack_team_id)
                failed += 1

    logger.info("Weekly reports: %d sent, %d failed", sent, failed)
    return {"sent": sent, "failed": failed}


def _send_report_dm(
    bot_token: str,
    user_id: str,
    stats: dict,
    week_start,
    week_end,
) -> None:
    """Send the weekly report DM to the decision-maker."""
    client = WebClient(token=bot_token)

    # Skip if no activity
    if stats["total_questions"] == 0:
        return

    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": f"주간 리포트 ({week_start.strftime('%m/%d')} ~ {week_end.strftime('%m/%d')})",
            },
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*총 질문:* {stats['total_questions']}개",
            },
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*검토 요청:* {stats['review_requests']}건",
            },
        },
        {"type": "divider"},
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": (
                    f"*피드백 현황:* {stats['feedback_completed']}건 완료\n"
                    f"  문제 없음: {stats['feedback_approved']}건\n"
                    f"  틀림: {stats['feedback_rejected']}건\n"
                    f"  직접 수정: {stats['feedback_corrected']}건\n"
                    f"  주의 필요: {stats['feedback_caution']}건"
                ),
            },
        },
        {
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": "실시간 현황은 `/slough-stats` 명령어로 확인할 수 있습니다.",
                },
            ],
        },
    ]

    try:
        dm = client.conversations_open(users=[user_id])
        channel_id = dm["channel"]["id"]
        client.chat_postMessage(
            channel=channel_id,
            blocks=blocks,
            text=f"주간 리포트 ({week_start.strftime('%m/%d')} ~ {week_end.strftime('%m/%d')})",
        )
    except SlackApiError:
        logger.exception("Failed to send weekly report DM to %s", user_id)
