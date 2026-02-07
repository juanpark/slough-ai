"""OAuth 2.0 helpers for Slack app installation."""

import logging
import secrets
import time
from urllib.parse import urlencode

from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

from src.config import settings
from src.services.db.connection import get_db
from src.services.db.workspaces import (
    create_workspace,
    get_workspace_by_team_id,
    update_workspace,
)

logger = logging.getLogger(__name__)

# All bot scopes the app needs
BOT_SCOPES = [
    "channels:history",
    "channels:read",
    "chat:write",
    "commands",
    "im:history",
    "im:read",
    "im:write",
    "users:read",
]

# In-memory state store for CSRF protection (MVP — single-process only)
_pending_states: dict[str, float] = {}
_STATE_TTL_SECONDS = 600  # 10 minutes


def generate_state() -> str:
    """Create a random state token and store it for later validation."""
    _cleanup_expired_states()
    state = secrets.token_urlsafe(32)
    _pending_states[state] = time.time()
    return state


def validate_state(state: str) -> bool:
    """Check that the state token is valid and consume it."""
    _cleanup_expired_states()
    created = _pending_states.pop(state, None)
    if created is None:
        return False
    return (time.time() - created) < _STATE_TTL_SECONDS


def _cleanup_expired_states() -> None:
    now = time.time()
    expired = [s for s, t in _pending_states.items() if (now - t) > _STATE_TTL_SECONDS]
    for s in expired:
        _pending_states.pop(s, None)


def build_authorize_url(state: str) -> str:
    """Build the Slack OAuth authorize URL."""
    params = {
        "client_id": settings.slack_client_id,
        "scope": ",".join(BOT_SCOPES),
        "redirect_uri": f"{settings.app_base_url}/slack/oauth_redirect",
        "state": state,
    }
    return f"https://slack.com/oauth/v2/authorize?{urlencode(params)}"


def exchange_code_for_token(code: str) -> dict:
    """Exchange the authorization code for an access token."""
    client = WebClient()
    response = client.oauth_v2_access(
        client_id=settings.slack_client_id,
        client_secret=settings.slack_client_secret,
        code=code,
        redirect_uri=f"{settings.app_base_url}/slack/oauth_redirect",
    )
    return response.data


def handle_installation(oauth_response: dict) -> None:
    """Create or update a workspace row from the OAuth response."""
    team_id = oauth_response["team"]["id"]
    team_name = oauth_response["team"]["name"]
    bot_token = oauth_response["access_token"]
    installer_id = oauth_response["authed_user"]["id"]

    with get_db() as db:
        existing = get_workspace_by_team_id(db, team_id)
        if existing:
            # Reactivate if previously uninstalled (within retention period)
            update_fields = dict(
                slack_team_name=team_name,
                admin_id=installer_id,
                bot_token=bot_token,
                uninstalled_at=None,
                data_deletion_at=None,
            )
            update_workspace(db, existing.id, **update_fields)
            if existing.uninstalled_at:
                logger.info("Reactivated workspace for team %s", team_id)
            else:
                logger.info("Updated workspace for team %s", team_id)
        else:
            create_workspace(
                db,
                slack_team_id=team_id,
                slack_team_name=team_name,
                admin_id=installer_id,
                decision_maker_id=installer_id,
                bot_token=bot_token,
            )
            logger.info("Created workspace for team %s", team_id)


def send_welcome_dm(bot_token: str, user_id: str) -> None:
    """Send an onboarding DM to the decision-maker after installation."""
    client = WebClient(token=bot_token)
    try:
        dm = client.conversations_open(users=[user_id])
        channel_id = dm["channel"]["id"]

        blocks = [
            {
                "type": "header",
                "text": {"type": "plain_text", "text": "Slough.ai 설치 완료"},
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": (
                        "안녕하세요! Slough.ai가 설치되었습니다.\n\n"
                        "저는 의사결정자의 Slack 대화를 학습하여, "
                        "의사결정자의 사고 방식을 반영한 답변을 제공합니다.\n\n"
                        f"*현재 학습 대상:* <@{user_id}>"
                    ),
                },
            },
            {"type": "divider"},
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": (
                        "*학습 시작 전 안내:*\n"
                        "- 봇이 추가된 공개 채널의 대화 기록을 분석합니다\n"
                        "- 학습 대상자의 메시지만 수집합니다\n"
                        "- 수집된 데이터는 이 워크스페이스 전용으로 사용됩니다\n"
                        "- 학습할 채널과 대상을 직접 선택할 수 있습니다"
                    ),
                },
            },
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "학습 설정 시작"},
                        "action_id": "start_onboarding",
                        "style": "primary",
                    },
                ],
            },
        ]

        client.chat_postMessage(
            channel=channel_id,
            blocks=blocks,
            text="Slough.ai가 설치되었습니다. 학습을 시작하려면 버튼을 클릭해 주세요.",
        )
        logger.info("Welcome DM sent to user %s", user_id)
    except SlackApiError:
        logger.exception("Failed to send welcome DM to user %s", user_id)
