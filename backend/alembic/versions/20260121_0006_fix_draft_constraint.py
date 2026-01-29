"""Replace draft exclude constraint with partial unique index.

Revision ID: 20260121_0006
Revises: 20250121_0005
Create Date: 2026-01-21 16:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '20260121_0006'
down_revision: Union[str, None] = '20250121_0005'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute('ALTER TABLE snapshots DROP CONSTRAINT IF EXISTS at_most_one_draft_per_project')
    op.create_index(
        'uniq_draft_per_project',
        'snapshots',
        ['project_id'],
        unique=True,
        postgresql_where=sa.text('is_draft = true'),
    )


def downgrade() -> None:
    op.drop_index('uniq_draft_per_project', table_name='snapshots')
    op.execute(
        """
        ALTER TABLE snapshots
        ADD CONSTRAINT at_most_one_draft_per_project
        EXCLUDE USING btree (project_id WITH =, is_draft WITH =)
        WHERE (is_draft = true)
        """
    )
