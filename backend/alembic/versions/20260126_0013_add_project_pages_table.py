"""Add project_pages table.

Revision ID: 20260126_0013
Revises: 20260126_0012
Create Date: 2026-01-26 12:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "20260126_0013"
down_revision: Union[str, None] = "20260126_0012"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "project_pages",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("slug", sa.String(length=100), nullable=True),
        sa.Column("path", sa.String(length=255), nullable=False, server_default="/"),
        sa.Column("is_home", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column(
            "content",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column(
            "design_system",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("project_id", "path", name="uq_project_pages_project_id_path"),
        sa.CheckConstraint(
            "slug IS NULL OR slug ~ '^[a-z0-9]([a-z0-9-]*[a-z0-9])?$'",
            name="project_page_slug_format",
        ),
    )
    op.create_index("ix_project_pages_project_id", "project_pages", ["project_id"])


def downgrade() -> None:
    op.drop_index("ix_project_pages_project_id", table_name="project_pages")
    op.drop_table("project_pages")
