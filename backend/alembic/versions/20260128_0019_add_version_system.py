"""Add version system tables.

Revision ID: 20260128_0019
Revises: 20260128_0018
Create Date: 2026-01-28 12:30:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "20260128_0019"
down_revision: Union[str, None] = "20260128_0018"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "branches",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "project_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("projects.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.String(length=50), nullable=False),
        sa.Column("label", sa.String(length=50), nullable=True),
        sa.Column(
            "parent_branch_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("branches.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "created_from_version_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
        ),
        sa.Column("is_default", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    op.create_index("idx_branches_project", "branches", ["project_id"])

    op.create_table(
        "version_snapshots",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "project_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("projects.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "snapshot_data",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    op.create_index(
        "idx_version_snapshots_project_created",
        "version_snapshots",
        ["project_id", "created_at"],
    )

    op.create_table(
        "versions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "project_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("projects.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "parent_version_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("versions.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "branch_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("branches.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("branch_label", sa.String(length=50), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("trigger_message_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column(
            "snapshot_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("version_snapshots.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "change_summary",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column(
            "validation_status",
            sa.String(length=20),
            nullable=False,
            server_default=sa.text("'pending'"),
        ),
        sa.Column(
            "is_pinned",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
    )
    op.create_index(
        "idx_versions_project_created",
        "versions",
        ["project_id", "created_at"],
    )
    op.create_index(
        "idx_versions_branch",
        "versions",
        ["branch_id", "created_at"],
    )
    op.create_index("idx_versions_trigger", "versions", ["trigger_message_id"])

    op.create_table(
        "version_diffs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "project_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("projects.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "version_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("versions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "base_version_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("versions.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("diff_text", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    op.create_index("idx_version_diffs_version", "version_diffs", ["version_id"])
    op.create_index("idx_version_diffs_base", "version_diffs", ["base_version_id"])


def downgrade() -> None:
    op.drop_index("idx_version_diffs_base", table_name="version_diffs")
    op.drop_index("idx_version_diffs_version", table_name="version_diffs")
    op.drop_table("version_diffs")

    op.drop_index("idx_versions_trigger", table_name="versions")
    op.drop_index("idx_versions_branch", table_name="versions")
    op.drop_index("idx_versions_project_created", table_name="versions")
    op.drop_table("versions")

    op.drop_index("idx_version_snapshots_project_created", table_name="version_snapshots")
    op.drop_table("version_snapshots")

    op.drop_index("idx_branches_project", table_name="branches")
    op.drop_table("branches")
