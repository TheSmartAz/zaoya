"""Normalize project_pages indexes.

Revision ID: 20260126_0014
Revises: 20260126_0013
Create Date: 2026-01-26 13:00:00.000000
"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "20260126_0014"
down_revision: Union[str, None] = "20260126_0013"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_project_pages_sort_order")
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_project_pages_project_id ON project_pages (project_id)"
    )


def downgrade() -> None:
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_project_pages_sort_order ON project_pages (project_id, sort_order)"
    )
