"""Handler for /stats slash command — shows real-time workspace statistics."""

import logging

from src.services.db import get_db
from src.services.db.workspaces import get_workspace_by_team_id
from src.services.db.weekly_stats import get_period_stats, get_current_week_range

logger = logging.getLogger(__name__)

FALLBACK_RESPONSE = "일시적인 오류가 발생했습니다. 잠시 후 다시 시도해 주세요."


def register(app):
    """Register the /stats command handler."""

    @app.command("/slough-stats")
    def handle_stats_command(ack, command, respond):
        ack()

        team_id = command.get("team_id", "")
        user_id = command.get("user_id", "")

        # Look up workspace
        try:
            with get_db() as db:
                workspace = get_workspace_by_team_id(db, team_id)
                if workspace is None:
                    respond("워크스페이스 설정이 완료되지 않았습니다.")
                    return
                admin_id = workspace.admin_id
                workspace_id = workspace.id
        except Exception:
            logger.exception("DB error during /stats")
            respond(FALLBACK_RESPONSE)
            return

        # Admin only
        if admin_id != user_id:
            respond("이 명령어는 앱 관리자만 사용할 수 있습니다.")
            return

        # Get current week stats
        try:
            week_start, week_end = get_current_week_range()
            with get_db() as db:
                stats = get_period_stats(db, workspace_id, week_start, week_end)
        except Exception:
            logger.exception("Failed to aggregate stats")
            respond(FALLBACK_RESPONSE)
            return

        respond(blocks=_build_stats_blocks(stats, week_start, week_end), text="주간 현황")


def _build_stats_blocks(stats: dict, week_start, week_end) -> list[dict]:
    """Build Block Kit blocks for the stats display."""
    return [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": f"이번 주 현황 ({week_start.strftime('%m/%d')} ~ {week_end.strftime('%m/%d')})",
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
    ]
