"""Add uninstalled_at and data_deletion_at to workspaces."""

from alembic import op
import sqlalchemy as sa

revision = "004"
down_revision = "003"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("workspaces", sa.Column("uninstalled_at", sa.DateTime, nullable=True))
    op.add_column("workspaces", sa.Column("data_deletion_at", sa.DateTime, nullable=True))


def downgrade():
    op.drop_column("workspaces", "data_deletion_at")
    op.drop_column("workspaces", "uninstalled_at")
