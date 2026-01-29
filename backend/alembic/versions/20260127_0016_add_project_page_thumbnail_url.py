"""Add thumbnail_url to project_pages.

Revision ID: 20260127_0016
Revises: 20260127_0015
Create Date: 2026-01-27 12:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "20260127_0016"
down_revision: Union[str, None] = "20260127_0015"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("project_pages", sa.Column("thumbnail_url", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("project_pages", "thumbnail_url")
