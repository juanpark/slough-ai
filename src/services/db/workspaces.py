"""Workspace CRUD operations."""

import uuid
from typing import Optional

from sqlalchemy.orm import Session

from src.services.db.models import Workspace


def get_workspace_by_team_id(db: Session, team_id: str) -> Optional[Workspace]:
    """Look up a workspace by its Slack team ID."""
    return db.query(Workspace).filter(Workspace.slack_team_id == team_id).first()


def create_workspace(db: Session, *, slack_team_id: str, slack_team_name: str,
                     decision_maker_id: str, bot_token: str, user_token: str) -> Workspace:
    """Insert a new workspace row."""
    ws = Workspace(
        id=uuid.uuid4(),
        slack_team_id=slack_team_id,
        slack_team_name=slack_team_name,
        decision_maker_id=decision_maker_id,
        bot_token=bot_token,
        user_token=user_token,
    )
    db.add(ws)
    db.flush()
    return ws


def update_workspace(db: Session, workspace_id: uuid.UUID, **fields) -> Optional[Workspace]:
    """Update workspace fields. Pass only the columns you want to change."""
    ws = db.query(Workspace).filter(Workspace.id == workspace_id).first()
    if ws is None:
        return None
    for key, value in fields.items():
        if hasattr(ws, key):
            setattr(ws, key, value)
    db.flush()
    return ws
