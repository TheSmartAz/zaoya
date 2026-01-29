"""Allow projects.active_branch_id to be nullable.

Revision ID: 20260129_0021
Revises: 20260129_0020
Create Date: 2026-01-29
"""

from alembic import op
import sqlalchemy as sa

revision = "20260129_0021"
down_revision = "20260129_0020"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column("projects", "active_branch_id", nullable=True)


def downgrade() -> None:
    op.alter_column("projects", "active_branch_id", nullable=False)
