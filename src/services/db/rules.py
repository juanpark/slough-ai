"""Rules CRUD operations."""

import uuid
from typing import Optional

from sqlalchemy.orm import Session

from src.services.db.models import Rule


def get_active_rules(db: Session, workspace_id: uuid.UUID) -> list[Rule]:
    """Return all active rules for a workspace, newest first."""
    return (
        db.query(Rule)
        .filter(Rule.workspace_id == workspace_id, Rule.is_active.is_(True))
        .order_by(Rule.id.desc())
        .all()
    )


def create_rule(db: Session, workspace_id: uuid.UUID, rule_text: str) -> Rule:
    """Insert a new rule."""
    rule = Rule(workspace_id=workspace_id, rule_text=rule_text)
    db.add(rule)
    db.flush()
    return rule


def delete_rule(db: Session, rule_id: int, workspace_id: uuid.UUID) -> bool:
    """Soft-delete a rule by marking it inactive. Returns True if found."""
    rule = (
        db.query(Rule)
        .filter(Rule.id == rule_id, Rule.workspace_id == workspace_id, Rule.is_active.is_(True))
        .first()
    )
    if rule is None:
        return False
    rule.is_active = False
    db.flush()
    return True
