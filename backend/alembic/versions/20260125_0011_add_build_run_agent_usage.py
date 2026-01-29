"""Add agent usage tracking to build_runs.

Revision ID: 20260125_0011
Revises: 20260125_0010
Create Date: 2026-01-25 13:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "20260125_0011"
down_revision: Union[str, None] = "20260125_0010"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("build_runs", sa.Column("agent_usage", postgresql.JSONB(), nullable=True))
    op.add_column("build_runs", sa.Column("last_agent_usage", postgresql.JSONB(), nullable=True))


def downgrade() -> None:
    op.drop_column("build_runs", "last_agent_usage")
    op.drop_column("build_runs", "agent_usage")
