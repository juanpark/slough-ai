"""Handler for /slough-ingest — incremental learning of decision-maker messages.

Fetches only NEW messages since the last successful ingestion, avoiding
duplicates. Runs ingestion in a background thread so ack() returns immediately.
"""

import logging
import threading
from datetime import datetime

from src.services.db import get_db
from src.services.db.workspaces import get_workspace_by_team_id
from src.services.db.ingestion_jobs import get_latest_job
from src.services.ingestion.ingest import run_ingestion

logger = logging.getLogger(__name__)


def register(app):
    """Register the /slough-ingest slash command."""

    @app.command("/slough-ingest")
    def handle_ingest(ack, command, respond, client):
        ack()

        team_id = command.get("team_id", "")
        user_id = command.get("user_id", "")

        # Look up workspace
        try:
            with get_db() as db:
                workspace = get_workspace_by_team_id(db, team_id)
                if workspace is None:
                    respond(text="❌ 워크스페이스를 찾을 수 없습니다.")
                    return

                # Only admin or decision-maker can run ingestion
                if user_id not in (workspace.admin_id, workspace.decision_maker_id):
                    respond(text="❌ 관리자 또는 의사결정자만 학습을 실행할 수 있습니다.")
                    return

                workspace_id = workspace.id

                # Check for running job
                latest_job = get_latest_job(db, workspace_id)
                if latest_job and latest_job.status == "running":
                    respond(text="⏳ 이미 학습이 진행 중입니다. 완료될 때까지 기다려 주세요.")
                    return

        except Exception:
            logger.exception("DB error during /slough-ingest")
            respond(text="❌ 데이터베이스 오류가 발생했습니다.")
            return

        # Start ingestion in background
        respond(
            text=(
                "📚 증분 학습을 시작합니다!\n"
                "이전 학습 이후 새로운 메시지만 가져옵니다.\n"
                "완료되면 DM으로 알려드리겠습니다."
            ),
        )

        threading.Thread(
            target=run_ingestion,
            args=(team_id,),
            kwargs={"incremental": True},
            daemon=True,
        ).start()
