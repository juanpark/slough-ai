"""Add IVFFlat index on embeddings for cosine similarity search."""

from alembic import op

revision = "006"
down_revision = "005"
branch_labels = None
depends_on = None


def upgrade():
    # IVFFlat index for fast approximate nearest-neighbour search.
    # The `lists` parameter should be tuned based on dataset size
    # (rule of thumb: sqrt(num_rows)).  100 is a safe default for
    # up to ~10 000 rows.
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_embeddings_cosine
        ON embeddings
        USING ivfflat (embedding vector_cosine_ops)
        WITH (lists = 100)
    """)


def downgrade():
    op.execute("DROP INDEX IF EXISTS ix_embeddings_cosine")
