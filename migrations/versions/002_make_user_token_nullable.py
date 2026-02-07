"""make user_token nullable

Revision ID: 002
Revises: 001
Create Date: 2026-02-07
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        "workspaces",
        "user_token",
        existing_type=sa.Text(),
        nullable=True,
        server_default=sa.text("''"),
    )


def downgrade() -> None:
    op.alter_column(
        "workspaces",
        "user_token",
        existing_type=sa.Text(),
        nullable=False,
        server_default=None,
    )
