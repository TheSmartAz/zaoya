"""Add simulation reports table and failed version metadata.

Revision ID: 20260129_0024
Revises: 20260129_0023
Create Date: 2026-01-29
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "20260129_0024"
down_revision = "20260129_0023"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "version_attempts",
        sa.Column("validation_errors", postgresql.JSONB(), nullable=True),
    )
    op.add_column(
        "version_attempts",
        sa.Column(
            "retry_of",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("version_attempts.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.create_index(
        "idx_version_attempts_retry_of",
        "version_attempts",
        ["retry_of"],
    )

    op.create_table(
        "simulation_reports",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "project_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("projects.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("report_type", sa.String(length=30), nullable=False),
        sa.Column("report", postgresql.JSONB(), nullable=False),
        sa.Column("user_agent", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(
        "idx_simulation_reports_project_created",
        "simulation_reports",
        ["project_id", "created_at"],
    )


def downgrade() -> None:
    op.drop_index("idx_simulation_reports_project_created", table_name="simulation_reports")
    op.drop_table("simulation_reports")

    op.drop_index("idx_version_attempts_retry_of", table_name="version_attempts")
    op.drop_column("version_attempts", "retry_of")
    op.drop_column("version_attempts", "validation_errors")
