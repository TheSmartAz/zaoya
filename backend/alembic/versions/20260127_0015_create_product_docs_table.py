"""Create product_docs table.

Revision ID: 20260127_0015
Revises: 20260126_0014
Create Date: 2026-01-27 10:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "20260127_0015"
down_revision: Union[str, None] = "20260126_0014"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "product_docs",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("updated_at", sa.DateTime, nullable=False),
        sa.Column("overview", sa.Text, nullable=False),
        sa.Column(
            "target_users",
            postgresql.JSONB(),
            nullable=True,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column(
            "content_structure",
            postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column("design_requirements", postgresql.JSONB(), nullable=True),
        sa.Column(
            "page_plan",
            postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column("technical_constraints", postgresql.JSONB(), nullable=True),
        sa.Column(
            "interview_answers",
            postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column("generation_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("last_generated_at", sa.DateTime, nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("project_id"),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
    )

    op.create_index("ix_product_docs_project_id", "product_docs", ["project_id"])


def downgrade() -> None:
    op.drop_index("ix_product_docs_project_id", table_name="product_docs")
    op.drop_table("product_docs")
