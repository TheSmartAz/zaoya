"""Add interview_state to snapshots.

Revision ID: 20260123_0009
Revises: 20260122_0008
Create Date: 2026-01-23 10:30:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "20260123_0009"
down_revision: Union[str, None] = "20260122_0008"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "snapshots",
        sa.Column("interview_state", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
    )
    op.alter_column("snapshots", "interview_state", server_default=None)


def downgrade() -> None:
    op.drop_column("snapshots", "interview_state")
