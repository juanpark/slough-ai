"""Onboarding modal submission handler — validates consent, updates workspace, starts ingestion."""

import json
import logging

from src.services.db.connection import get_db
from src.services.db.workspaces import get_workspace_by_team_id, update_workspace
from src.tasks.ingestion import ingest_workspace_task

logger = logging.getLogger(__name__)


def register(app):
    """Register the onboarding modal submission handler."""

    @app.view("onboarding_submit")
    def handle_onboarding_submit(ack, body, client, view):
        values = view["state"]["values"]
        user_id = body["user"]["id"]
        team_id = body["user"].get("team_id")

        # Extract values from input blocks
        decision_maker_id = (
            values["dm_select_block"]["decision_maker_select"].get("selected_user")
        )
        channels = (
            values["channel_select_block"]["channel_select"]
            .get("selected_conversations", [])
        )
        consent_options = (
            values["consent_block"]["consent_check"].get("selected_options", [])
        )
        consent = any(opt.get("value") == "consent_given" for opt in consent_options)

        # Validate consent
        if not consent:
            ack(
                response_action="errors",
                errors={"consent_block": "학습을 시작하려면 동의가 필요합니다."},
            )
            return

        # Validate channels
        if not channels:
            ack(
                response_action="errors",
                errors={"channel_select_block": "최소 1개의 채널을 선택해 주세요."},
            )
            return

        ack()

        # Update decision-maker if changed
        if team_id and decision_maker_id:
            with get_db() as db:
                workspace = get_workspace_by_team_id(db, team_id)
                if workspace and workspace.decision_maker_id != decision_maker_id:
                    update_workspace(db, workspace.id, decision_maker_id=decision_maker_id)
                    logger.info(
                        "Decision-maker changed to %s for team %s",
                        decision_maker_id, team_id,
                    )

        # Queue ingestion with selected channels
        ingest_workspace_task.delay(team_id, channel_ids=channels)
        logger.info(
            "Queued ingestion for team %s: %d channels, decision_maker=%s",
            team_id, len(channels), decision_maker_id,
        )

        # Notify the user that ingestion has started
        try:
            dm = client.conversations_open(users=[user_id])
            channel_id = dm["channel"]["id"]
            client.chat_postMessage(
                channel=channel_id,
                text=(
                    f"학습을 시작합니다!\n\n"
                    f"- 학습 대상: <@{decision_maker_id}>\n"
                    f"- 선택된 채널: {len(channels)}개\n\n"
                    f"학습이 완료되면 알려드리겠습니다. "
                    f"채널 수와 메시지 양에 따라 몇 분 정도 소요될 수 있습니다."
                ),
            )
        except Exception:
            logger.exception("Failed to send ingestion start DM")
