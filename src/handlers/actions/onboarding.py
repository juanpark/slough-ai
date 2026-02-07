"""Onboarding action handler — opens the learning setup modal."""

import logging

from src.services.db.connection import get_db
from src.services.db.workspaces import get_workspace_by_team_id

logger = logging.getLogger(__name__)


def register(app):
    """Register the onboarding button handler."""

    @app.action("start_onboarding")
    def handle_start_onboarding(ack, body, client):
        ack()

        trigger_id = body["trigger_id"]
        team_id = body.get("team", {}).get("id")
        user_id = body["user"]["id"]

        # Look up workspace and check admin permission
        current_dm_id = user_id
        if team_id:
            with get_db() as db:
                workspace = get_workspace_by_team_id(db, team_id)
                if workspace:
                    if workspace.admin_id != user_id:
                        client.chat_postEphemeral(
                            channel=body["channel"]["id"],
                            user=user_id,
                            text="이 설정은 앱 관리자만 변경할 수 있습니다.",
                        )
                        return
                    current_dm_id = workspace.decision_maker_id

        client.views_open(
            trigger_id=trigger_id,
            view={
                "type": "modal",
                "callback_id": "onboarding_submit",
                "title": {"type": "plain_text", "text": "학습 설정"},
                "submit": {"type": "plain_text", "text": "학습 시작"},
                "close": {"type": "plain_text", "text": "취소"},
                "blocks": [
                    {
                        "type": "input",
                        "block_id": "dm_select_block",
                        "label": {
                            "type": "plain_text",
                            "text": "학습 대상 (의사결정자)",
                        },
                        "element": {
                            "type": "users_select",
                            "action_id": "decision_maker_select",
                            "initial_user": current_dm_id,
                            "placeholder": {
                                "type": "plain_text",
                                "text": "누구의 사고 방식을 학습할지 선택해 주세요",
                            },
                        },
                    },
                    {"type": "divider"},
                    {
                        "type": "input",
                        "block_id": "channel_select_block",
                        "label": {
                            "type": "plain_text",
                            "text": "학습할 채널 (복수 선택 가능)",
                        },
                        "hint": {
                            "type": "plain_text",
                            "text": "여러 채널을 선택하면 더 정확한 학습이 가능합니다.",
                        },
                        "element": {
                            "type": "multi_conversations_select",
                            "action_id": "channel_select",
                            "placeholder": {
                                "type": "plain_text",
                                "text": "채널을 클릭하여 여러 개 선택",
                            },
                            "filter": {
                                "include": ["public"],
                                "exclude_bot_users": True,
                            },
                        },
                    },
                    {"type": "divider"},
                    {
                        "type": "input",
                        "block_id": "consent_block",
                        "label": {
                            "type": "plain_text",
                            "text": "동의",
                        },
                        "element": {
                            "type": "checkboxes",
                            "action_id": "consent_check",
                            "options": [
                                {
                                    "text": {
                                        "type": "mrkdwn",
                                        "text": "선택한 채널에서 학습 대상자의 메시지를 수집하고 분석하는 것에 동의합니다.",
                                    },
                                    "value": "consent_given",
                                },
                            ],
                        },
                    },
                    {
                        "type": "context",
                        "elements": [
                            {
                                "type": "mrkdwn",
                                "text": "수집된 데이터는 이 워크스페이스 전용이며, 팀원 질문에 대한 AI 답변 생성에만 사용됩니다.",
                            },
                        ],
                    },
                ],
            },
        )
