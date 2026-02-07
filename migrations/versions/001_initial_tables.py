"""initial tables

Revision ID: 001
Revises:
Create Date: 2026-02-07
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')

    op.create_table(
        "workspaces",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("uuid_generate_v4()"), nullable=False),
        sa.Column("slack_team_id", sa.String(20), nullable=False),
        sa.Column("slack_team_name", sa.String(255)),
        sa.Column("decision_maker_id", sa.String(20), nullable=False),
        sa.Column("bot_token", sa.Text(), nullable=False),
        sa.Column("user_token", sa.Text(), nullable=False),
        sa.Column("installed_at", sa.DateTime(), server_default=sa.text("now()")),
        sa.Column("onboarding_completed", sa.Boolean(), server_default=sa.text("false")),
        sa.Column("onboarding_completed_at", sa.DateTime()),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("slack_team_id"),
    )

    op.create_table(
        "rules",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("workspace_id", postgresql.UUID(as_uuid=True)),
        sa.Column("rule_text", sa.Text(), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], ondelete="CASCADE"),
    )
    op.create_index("rules_workspace_active_idx", "rules", ["workspace_id", "is_active"])

    op.create_table(
        "qa_history",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("uuid_generate_v4()"), nullable=False),
        sa.Column("workspace_id", postgresql.UUID(as_uuid=True)),
        sa.Column("asker_user_id", sa.String(20), nullable=False),
        sa.Column("asker_user_name", sa.String(255)),
        sa.Column("question", sa.Text(), nullable=False),
        sa.Column("answer", sa.Text(), nullable=False),
        sa.Column("message_ts", sa.String(20)),
        sa.Column("channel_id", sa.String(20)),
        sa.Column("review_status", sa.String(20), server_default=sa.text("'none'")),
        sa.Column("review_requested_at", sa.DateTime()),
        sa.Column("feedback_type", sa.String(20)),
        sa.Column("corrected_answer", sa.Text()),
        sa.Column("feedback_at", sa.DateTime()),
        sa.Column("is_high_risk", sa.Boolean(), server_default=sa.text("false")),
        sa.Column("matched_rule_id", sa.Integer()),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["matched_rule_id"], ["rules.id"]),
    )
    op.create_index("qa_history_workspace_idx", "qa_history", ["workspace_id"])
    op.create_index("qa_history_review_status_idx", "qa_history", ["workspace_id", "review_status"])
    op.create_index("qa_history_created_at_idx", "qa_history", ["workspace_id", "created_at"])

    op.create_table(
        "weekly_stats",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("workspace_id", postgresql.UUID(as_uuid=True)),
        sa.Column("week_start", sa.Date(), nullable=False),
        sa.Column("week_end", sa.Date(), nullable=False),
        sa.Column("total_questions", sa.Integer(), server_default=sa.text("0")),
        sa.Column("review_requests", sa.Integer(), server_default=sa.text("0")),
        sa.Column("feedback_completed", sa.Integer(), server_default=sa.text("0")),
        sa.Column("feedback_approved", sa.Integer(), server_default=sa.text("0")),
        sa.Column("feedback_rejected", sa.Integer(), server_default=sa.text("0")),
        sa.Column("feedback_corrected", sa.Integer(), server_default=sa.text("0")),
        sa.Column("feedback_caution", sa.Integer(), server_default=sa.text("0")),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("workspace_id", "week_start"),
    )

    op.create_table(
        "ingestion_jobs",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("uuid_generate_v4()"), nullable=False),
        sa.Column("workspace_id", postgresql.UUID(as_uuid=True)),
        sa.Column("status", sa.String(20), server_default=sa.text("'pending'")),
        sa.Column("total_channels", sa.Integer(), server_default=sa.text("0")),
        sa.Column("processed_channels", sa.Integer(), server_default=sa.text("0")),
        sa.Column("total_messages", sa.Integer(), server_default=sa.text("0")),
        sa.Column("processed_messages", sa.Integer(), server_default=sa.text("0")),
        sa.Column("error_message", sa.Text()),
        sa.Column("started_at", sa.DateTime()),
        sa.Column("completed_at", sa.DateTime()),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], ondelete="CASCADE"),
    )

    # Triggers for updated_at (workspaces, rules)
    op.execute("""
        CREATE OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = NOW();
            RETURN NEW;
        END;
        $$ language 'plpgsql'
    """)
    op.execute("""
        CREATE TRIGGER update_workspaces_updated_at
            BEFORE UPDATE ON workspaces
            FOR EACH ROW EXECUTE FUNCTION update_updated_at_column()
    """)
    op.execute("""
        CREATE TRIGGER update_rules_updated_at
            BEFORE UPDATE ON rules
            FOR EACH ROW EXECUTE FUNCTION update_updated_at_column()
    """)


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS update_rules_updated_at ON rules")
    op.execute("DROP TRIGGER IF EXISTS update_workspaces_updated_at ON workspaces")
    op.execute("DROP FUNCTION IF EXISTS update_updated_at_column()")
    op.drop_table("ingestion_jobs")
    op.drop_table("weekly_stats")
    op.drop_table("qa_history")
    op.drop_table("rules")
    op.drop_table("workspaces")
