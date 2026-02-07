"""Add pgvector extension and embeddings table."""

from alembic import op
import sqlalchemy as sa

revision = "005"
down_revision = "004"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.execute("""
        CREATE TABLE embeddings (
            id SERIAL PRIMARY KEY,
            workspace_id UUID NOT NULL REFERENCES workspaces(id),
            content TEXT NOT NULL,
            embedding vector(1536) NOT NULL,
            channel_id VARCHAR(64),
            message_ts VARCHAR(64),
            thread_ts VARCHAR(64),
            created_at TIMESTAMP DEFAULT NOW()
        )
    """)
    op.execute("CREATE INDEX ix_embeddings_workspace_id ON embeddings (workspace_id)")


def downgrade():
    op.drop_table("embeddings")
    op.execute("DROP EXTENSION IF EXISTS vector")
