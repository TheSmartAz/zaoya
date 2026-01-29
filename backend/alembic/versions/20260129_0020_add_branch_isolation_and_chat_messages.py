"""Add chat messages, failed version attempts, and branch isolation.

Revision ID: 20260129_0020
Revises: 20260128_0019
Create Date: 2026-01-29
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from uuid import uuid4

# revision identifiers, used by Alembic.
revision = "20260129_0020"
down_revision = "20260128_0019"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "chat_messages",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "project_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("projects.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("role", sa.String(length=20), nullable=False),
        sa.Column("action", sa.String(length=50), nullable=True),
        sa.Column("content", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(
        "idx_chat_messages_project_created",
        "chat_messages",
        ["project_id", "created_at"],
    )
    op.create_index(
        "idx_chat_messages_user_project_created",
        "chat_messages",
        ["user_id", "project_id", "created_at"],
    )

    op.create_table(
        "version_attempts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "project_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("projects.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "branch_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("branches.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "parent_version_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("versions.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "trigger_message_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("chat_messages.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("snapshot_data", postgresql.JSONB(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(
        "idx_version_attempts_project_created",
        "version_attempts",
        ["project_id", "created_at"],
    )
    op.create_index(
        "idx_version_attempts_branch_created",
        "version_attempts",
        ["branch_id", "created_at"],
    )

    op.add_column(
        "projects",
        sa.Column(
            "active_branch_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("branches.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.add_column(
        "project_pages",
        sa.Column(
            "branch_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("branches.id", ondelete="CASCADE"),
            nullable=True,
        ),
    )
    op.create_index(
        "idx_project_pages_branch",
        "project_pages",
        ["branch_id", "sort_order"],
    )

    bind = op.get_bind()
    project_rows = bind.execute(sa.text("SELECT id FROM projects")).fetchall()
    for row in project_rows:
        project_id = row[0]
        branch_row = bind.execute(
            sa.text(
                "SELECT id FROM branches WHERE project_id = :pid AND is_default = true"
            ),
            {"pid": project_id},
        ).fetchone()
        if branch_row:
            branch_id = branch_row[0]
        else:
            branch_id = uuid4()
            bind.execute(
                sa.text(
                    """
                    INSERT INTO branches (id, project_id, name, label, parent_branch_id, created_from_version_id, is_default, created_at)
                    VALUES (:id, :project_id, :name, :label, NULL, NULL, true, NOW())
                    """
                ),
                {
                    "id": branch_id,
                    "project_id": project_id,
                    "name": "main",
                    "label": "Main",
                },
            )

        bind.execute(
            sa.text(
                "UPDATE projects SET active_branch_id = :branch_id WHERE id = :project_id AND active_branch_id IS NULL"
            ),
            {"branch_id": branch_id, "project_id": project_id},
        )
        bind.execute(
            sa.text(
                "UPDATE project_pages SET branch_id = :branch_id WHERE project_id = :project_id AND branch_id IS NULL"
            ),
            {"branch_id": branch_id, "project_id": project_id},
        )

    op.alter_column("projects", "active_branch_id", nullable=False)
    op.alter_column("project_pages", "branch_id", nullable=False)


def downgrade() -> None:
    op.drop_index("idx_project_pages_branch", table_name="project_pages")
    op.drop_column("project_pages", "branch_id")
    op.drop_column("projects", "active_branch_id")

    op.drop_index("idx_version_attempts_branch_created", table_name="version_attempts")
    op.drop_index("idx_version_attempts_project_created", table_name="version_attempts")
    op.drop_table("version_attempts")

    op.drop_index("idx_chat_messages_user_project_created", table_name="chat_messages")
    op.drop_index("idx_chat_messages_project_created", table_name="chat_messages")
    op.drop_table("chat_messages")
