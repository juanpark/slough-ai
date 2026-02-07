"""Handler for /rule slash command — add, list, delete rules."""

import logging
import re

from src.services.db import get_db
from src.services.db.workspaces import get_workspace_by_team_id
from src.services.db.rules import get_active_rules, create_rule, delete_rule

logger = logging.getLogger(__name__)


def register(app):
    """Register the /rule command handler on the Bolt app."""

    @app.command("/rule")
    def handle_rule_command(ack, command, say):
        ack()

        raw_text = (command.get("text") or "").strip()
        team_id = command.get("team_id", "")

        # Look up workspace
        with get_db() as db:
            workspace = get_workspace_by_team_id(db, team_id)

        if workspace is None:
            say("워크스페이스 설정이 완료되지 않았습니다.")
            return

        workspace_id = workspace.id

        if not raw_text:
            say(_help_text())
            return

        parts = raw_text.split(None, 1)
        subcommand = parts[0].lower()

        if subcommand == "add":
            _handle_add(workspace_id, parts, say)
        elif subcommand == "list":
            _handle_list(workspace_id, say)
        elif subcommand == "delete":
            _handle_delete(workspace_id, parts, say)
        else:
            say(_help_text())


def _handle_add(workspace_id, parts: list[str], say):
    if len(parts) < 2:
        say("사용법: `/rule add \"규칙 내용\"`")
        return

    rule_text = parts[1].strip()
    # Strip surrounding quotes if present
    match = re.match(r'^["\'](.+)["\']$', rule_text)
    if match:
        rule_text = match.group(1)

    if not rule_text:
        say("규칙 내용을 입력해 주세요.")
        return

    with get_db() as db:
        rule = create_rule(db, workspace_id, rule_text)
        rule_id = rule.id

    say(f"✅ 규칙이 추가되었습니다. (ID: {rule_id})\n> {rule_text}")


def _handle_list(workspace_id, say):
    with get_db() as db:
        rules = get_active_rules(db, workspace_id)

    if not rules:
        say("등록된 규칙이 없습니다. `/rule add \"규칙 내용\"`으로 추가하세요.")
        return

    lines = ["*등록된 규칙 목록:*"]
    for rule in rules:
        lines.append(f"  `{rule.id}` — {rule.rule_text}")

    say("\n".join(lines))


def _handle_delete(workspace_id, parts: list[str], say):
    if len(parts) < 2:
        say("사용법: `/rule delete [ID]`")
        return

    try:
        rule_id = int(parts[1].strip())
    except ValueError:
        say("규칙 ID는 숫자여야 합니다.")
        return

    with get_db() as db:
        deleted = delete_rule(db, rule_id, workspace_id)

    if not deleted:
        say(f"ID {rule_id}에 해당하는 규칙을 찾을 수 없습니다.")
        return

    say(f"🗑️ 규칙이 삭제되었습니다. (ID: {rule_id})")


def _help_text() -> str:
    return (
        "*`/rule` 명령어 사용법:*\n"
        "• `/rule add \"규칙 내용\"` — 새 규칙 추가\n"
        "• `/rule list` — 등록된 규칙 목록\n"
        "• `/rule delete [ID]` — 규칙 삭제"
    )
