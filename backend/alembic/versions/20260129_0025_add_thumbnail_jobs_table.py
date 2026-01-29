"""Add thumbnail jobs queue table.

Revision ID: 20260129_0025
Revises: 20260129_0024
Create Date: 2026-01-29
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "20260129_0025"
down_revision = "20260129_0024"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "thumbnail_jobs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "project_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("projects.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("page_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("type", sa.String(length=20), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("attempts", sa.Integer(), server_default="0", nullable=False),
        sa.Column("max_attempts", sa.Integer(), server_default="3", nullable=False),
        sa.Column("next_run_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("image_url", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(
        "idx_thumbnail_jobs_project_type",
        "thumbnail_jobs",
        ["project_id", "type"],
    )
    op.create_index(
        "idx_thumbnail_jobs_page_type",
        "thumbnail_jobs",
        ["page_id", "type"],
    )
    op.create_index(
        "idx_thumbnail_jobs_status_next_run",
        "thumbnail_jobs",
        ["status", "next_run_at"],
    )


def downgrade() -> None:
    op.drop_index("idx_thumbnail_jobs_status_next_run", table_name="thumbnail_jobs")
    op.drop_index("idx_thumbnail_jobs_page_type", table_name="thumbnail_jobs")
    op.drop_index("idx_thumbnail_jobs_project_type", table_name="thumbnail_jobs")
    op.drop_table("thumbnail_jobs")
