"""Handler for /rule slash command — add, list, delete rules."""

import logging
import re

from src.services.db import get_db
from src.services.db.workspaces import get_workspace_by_team_id
from src.services.db.rules import get_active_rules, create_rule, delete_rule

logger = logging.getLogger(__name__)

FALLBACK_RESPONSE = "일시적인 오류가 발생했습니다. 잠시 후 다시 시도해 주세요."


def register(app):
    """Register the /rule command handler on the Bolt app."""

    @app.command("/slough-rule")
    def handle_rule_command(ack, command, respond):
        ack()

        raw_text = (command.get("text") or "").strip()
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
            logger.exception("DB error during workspace lookup for /rule")
            respond(FALLBACK_RESPONSE)
            return

        # Only the app admin can manage rules
        if admin_id != user_id:
            respond("이 명령어는 앱 관리자만 사용할 수 있습니다.")
            return

        if not raw_text:
            respond(_help_text())
            return

        parts = raw_text.split(None, 1)
        subcommand = parts[0].lower()

        if subcommand == "add":
            _handle_add(workspace_id, parts, respond)
        elif subcommand == "list":
            _handle_list(workspace_id, respond)
        elif subcommand == "delete":
            _handle_delete(workspace_id, parts, respond)
        else:
            respond(_help_text())


def _handle_add(workspace_id, parts: list[str], respond):
    if len(parts) < 2:
        respond("사용법: `/slough-rule add \"규칙 내용\"`")
        return

    rule_text = parts[1].strip()
    # Strip surrounding quotes if present
    match = re.match(r'^["\'](.+)["\']$', rule_text)
    if match:
        rule_text = match.group(1)

    if not rule_text:
        respond("규칙 내용을 입력해 주세요.")
        return

    try:
        with get_db() as db:
            rule = create_rule(db, workspace_id, rule_text)
            rule_id = rule.id
    except Exception:
        logger.exception("Failed to create rule")
        respond(FALLBACK_RESPONSE)
        return

    respond(f"규칙이 추가되었습니다. (ID: {rule_id})\n> {rule_text}")


def _handle_list(workspace_id, respond):
    try:
        with get_db() as db:
            rules = get_active_rules(db, workspace_id)
    except Exception:
        logger.exception("Failed to list rules")
        respond(FALLBACK_RESPONSE)
        return

    if not rules:
        respond("등록된 규칙이 없습니다. `/slough-rule add \"규칙 내용\"`으로 추가하세요.")
        return

    lines = ["*등록된 규칙 목록:*"]
    for rule in rules:
        lines.append(f"  `{rule.id}` — {rule.rule_text}")

    respond("\n".join(lines))


def _handle_delete(workspace_id, parts: list[str], respond):
    if len(parts) < 2:
        respond("사용법: `/slough-rule delete [ID]`")
        return

    try:
        rule_id = int(parts[1].strip())
    except ValueError:
        respond("규칙 ID는 숫자여야 합니다.")
        return

    try:
        with get_db() as db:
            deleted = delete_rule(db, rule_id, workspace_id)
    except Exception:
        logger.exception("Failed to delete rule")
        respond(FALLBACK_RESPONSE)
        return

    if not deleted:
        respond(f"ID {rule_id}에 해당하는 규칙을 찾을 수 없습니다.")
        return

    respond(f"규칙이 삭제되었습니다. (ID: {rule_id})")


def _help_text() -> str:
    return (
        "*`/slough-rule` 명령어 사용법:*\n"
        "• `/slough-rule add \"규칙 내용\"` — 새 규칙 추가\n"
        "• `/rule list` — 등록된 규칙 목록\n"
        "• `/slough-rule delete [ID]` — 규칙 삭제"
    )
