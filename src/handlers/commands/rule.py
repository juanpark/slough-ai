"""Handler for /rule slash command — add, list, delete rules.

Uses in-memory storage for now (no DB yet). Will be replaced with DB CRUD.
"""

import logging
import re

logger = logging.getLogger(__name__)

# In-memory rule storage: {workspace_id: {rule_id: rule_text}}
_rules_store: dict[str, dict[int, str]] = {}
_next_id: dict[str, int] = {}


def _get_workspace_rules(workspace_id: str) -> dict[int, str]:
    if workspace_id not in _rules_store:
        _rules_store[workspace_id] = {}
        _next_id[workspace_id] = 1
    return _rules_store[workspace_id]


def _allocate_id(workspace_id: str) -> int:
    _get_workspace_rules(workspace_id)  # ensure initialized
    rule_id = _next_id[workspace_id]
    _next_id[workspace_id] = rule_id + 1
    return rule_id


def register(app):
    """Register the /rule command handler on the Bolt app."""

    @app.command("/rule")
    def handle_rule_command(ack, command, say):
        ack()

        raw_text = (command.get("text") or "").strip()
        # TODO: workspace_id from DB via team_id
        workspace_id = command.get("team_id", "stub-workspace")

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


def _handle_add(workspace_id: str, parts: list[str], say):
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

    rules = _get_workspace_rules(workspace_id)
    rule_id = _allocate_id(workspace_id)
    rules[rule_id] = rule_text

    say(f"✅ 규칙이 추가되었습니다. (ID: {rule_id})\n> {rule_text}")


def _handle_list(workspace_id: str, say):
    rules = _get_workspace_rules(workspace_id)

    if not rules:
        say("등록된 규칙이 없습니다. `/rule add \"규칙 내용\"`으로 추가하세요.")
        return

    lines = ["*등록된 규칙 목록:*"]
    for rule_id, rule_text in rules.items():
        lines.append(f"  `{rule_id}` — {rule_text}")

    say("\n".join(lines))


def _handle_delete(workspace_id: str, parts: list[str], say):
    if len(parts) < 2:
        say("사용법: `/rule delete [ID]`")
        return

    try:
        rule_id = int(parts[1].strip())
    except ValueError:
        say("규칙 ID는 숫자여야 합니다.")
        return

    rules = _get_workspace_rules(workspace_id)

    if rule_id not in rules:
        say(f"ID {rule_id}에 해당하는 규칙을 찾을 수 없습니다.")
        return

    deleted_text = rules.pop(rule_id)
    say(f"🗑️ 규칙이 삭제되었습니다. (ID: {rule_id})\n> {deleted_text}")


def _help_text() -> str:
    return (
        "*`/rule` 명령어 사용법:*\n"
        "• `/rule add \"규칙 내용\"` — 새 규칙 추가\n"
        "• `/rule list` — 등록된 규칙 목록\n"
        "• `/rule delete [ID]` — 규칙 삭제"
    )
