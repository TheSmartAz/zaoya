"""Add owner_id and render_templates to projects.

Revision ID: 20260128_0018
Revises: 20260127_0017
Create Date: 2026-01-28 09:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "20260128_0018"
down_revision: Union[str, None] = "20260127_0017"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "projects",
        sa.Column("owner_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.add_column(
        "projects",
        sa.Column(
            "render_templates",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
            server_default=sa.text(
                "'{\"preview\":\"preview_template_v1\",\"publish\":\"publish_template_v1\"}'::jsonb"
            ),
        ),
    )

    # Backfill owner_id from user_id
    op.execute("UPDATE projects SET owner_id = user_id WHERE owner_id IS NULL")
    op.execute(
        "UPDATE projects SET render_templates = "
        "'{\"preview\":\"preview_template_v1\",\"publish\":\"publish_template_v1\"}'::jsonb "
        "WHERE render_templates IS NULL"
    )

    op.alter_column("projects", "owner_id", nullable=False)
    op.alter_column(
        "projects",
        "render_templates",
        nullable=False,
        server_default=sa.text(
            "'{\"preview\":\"preview_template_v1\",\"publish\":\"publish_template_v1\"}'::jsonb"
        ),
    )

    op.create_foreign_key(
        "fk_projects_owner_id",
        "projects",
        "users",
        ["owner_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_index("ix_projects_owner_id", "projects", ["owner_id"])


def downgrade() -> None:
    op.drop_index("ix_projects_owner_id", table_name="projects")
    op.drop_constraint("fk_projects_owner_id", "projects", type_="foreignkey")
    op.drop_column("projects", "render_templates")
    op.drop_column("projects", "owner_id")
