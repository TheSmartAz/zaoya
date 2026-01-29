"""Create build_runs table.

Revision ID: 20260125_0010
Revises: 20260123_0009
Create Date: 2026-01-25 12:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "20260125_0010"
down_revision: Union[str, None] = "20260123_0009"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "build_runs",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("build_id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("phase", sa.String(20), nullable=False, server_default="planning"),
        sa.Column("current_task_id", sa.String(50), nullable=True),
        sa.Column("brief", postgresql.JSONB(), nullable=True),
        sa.Column("build_plan", postgresql.JSONB(), nullable=True),
        sa.Column("product_doc", postgresql.JSONB(), nullable=True),
        sa.Column("build_graph", postgresql.JSONB(), nullable=True),
        sa.Column("patch_sets", postgresql.JSONB(), nullable=True),
        sa.Column("last_patch", postgresql.JSONB(), nullable=True),
        sa.Column("validation_reports", postgresql.JSONB(), nullable=True),
        sa.Column("last_validation", postgresql.JSONB(), nullable=True),
        sa.Column("check_reports", postgresql.JSONB(), nullable=True),
        sa.Column("last_checks", postgresql.JSONB(), nullable=True),
        sa.Column("review_reports", postgresql.JSONB(), nullable=True),
        sa.Column("last_review", postgresql.JSONB(), nullable=True),
        sa.Column("history", postgresql.JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("updated_at", sa.DateTime, nullable=False),
        sa.Column("completed_at", sa.DateTime, nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("build_id"),
    )

    op.create_index("ix_build_runs_project_phase", "build_runs", ["project_id", "phase"])
    op.create_index("ix_build_runs_created_at", "build_runs", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_build_runs_created_at", table_name="build_runs")
    op.drop_index("ix_build_runs_project_phase", table_name="build_runs")
    op.drop_table("build_runs")
