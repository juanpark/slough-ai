"""Add is_reflected column to qa_history for feedback sync tracking.

Revision ID: 007
Revises: 006
"""

from alembic import op
import sqlalchemy as sa


revision = "007"
down_revision = "006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "qa_history",
        sa.Column("is_reflected", sa.Boolean(), server_default=sa.text("false"), nullable=False),
    )


def downgrade() -> None:
    op.drop_column("qa_history", "is_reflected")
