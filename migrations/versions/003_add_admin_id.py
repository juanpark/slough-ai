"""add admin_id to workspaces

Revision ID: 003
Revises: 002
Create Date: 2026-02-07
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add column as nullable first
    op.add_column(
        "workspaces",
        sa.Column("admin_id", sa.String(20), nullable=True),
    )
    # Copy decision_maker_id to admin_id for existing rows
    op.execute("UPDATE workspaces SET admin_id = decision_maker_id WHERE admin_id IS NULL")
    # Now make it non-nullable
    op.alter_column("workspaces", "admin_id", nullable=False)


def downgrade() -> None:
    op.drop_column("workspaces", "admin_id")
