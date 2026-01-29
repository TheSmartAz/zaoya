"""Add build_plans table.

Revision ID: 20260127_0017
Revises: 20260127_0016
Create Date: 2026-01-27 12:30:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "20260127_0017"
down_revision: Union[str, None] = "20260127_0016"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    buildstatus = postgresql.ENUM(
        "draft",
        "approved",
        "running",
        "completed",
        "failed",
        "cancelled",
        name="buildstatus",
        create_type=False,
    )
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'buildstatus') THEN
                CREATE TYPE buildstatus AS ENUM ('draft', 'approved', 'running', 'completed', 'failed', 'cancelled');
            END IF;
        END $$;
        """
    )

    op.create_table(
        "build_plans",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("pages", postgresql.JSONB(), nullable=True),
        sa.Column("tasks", postgresql.JSONB(), nullable=True),
        sa.Column("total_tasks", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("completed_tasks", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("failed_tasks", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("estimated_duration_ms", sa.Integer(), nullable=True),
        sa.Column("actual_duration_ms", sa.Integer(), nullable=True),
        sa.Column("started_at", sa.DateTime, nullable=True),
        sa.Column("completed_at", sa.DateTime, nullable=True),
        sa.Column("status", buildstatus, nullable=False, server_default="draft"),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
    )

    op.create_index("ix_build_plans_project_id", "build_plans", ["project_id"])


def downgrade() -> None:
    op.drop_index("ix_build_plans_project_id", table_name="build_plans")
    op.drop_table("build_plans")

    buildstatus = postgresql.ENUM(
        "draft",
        "approved",
        "running",
        "completed",
        "failed",
        "cancelled",
        name="buildstatus",
        create_type=False,
    )
    buildstatus.drop(op.get_bind(), checkfirst=True)
