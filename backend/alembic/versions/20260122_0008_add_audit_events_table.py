"""Add audit_events table for activity logging.

Revision ID: 20260122_0008
Revises: 20260122_0007
Create Date: 2026-01-22 10:05:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '20260122_0008'
down_revision: Union[str, None] = '20260122_0007'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create audit_events table for future-proofing team collaboration
    op.create_table(
        'audit_events',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True),  # Can be NULL for system actions
        sa.Column('team_id', postgresql.UUID(as_uuid=True), nullable=True),  # Future: for team support
        # Action details
        sa.Column('action', sa.String(50), nullable=False),
        sa.Column('resource_type', sa.String(50), nullable=False),
        sa.Column('resource_id', postgresql.UUID(as_uuid=True), nullable=True),
        # Additional context
        sa.Column('metadata', postgresql.JSONB(), nullable=True),
        sa.Column('ip_address', sa.String(45), nullable=True),  # IPv6 compatible
        sa.Column('user_agent', sa.String(500), nullable=True),
        # Timestamp
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        # Primary key
        sa.PrimaryKeyConstraint('id'),
        # Foreign key to users (SET NULL on delete to preserve audit history)
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
    )

    # Create indexes for common query patterns
    op.create_index('idx_audit_events_user_id', 'audit_events', ['user_id'])
    op.create_index('idx_audit_events_resource', 'audit_events', ['resource_type', 'resource_id'])
    op.create_index('idx_audit_events_created_at', 'audit_events', ['created_at'])
    op.create_index('idx_audit_events_action', 'audit_events', ['action'])


def downgrade() -> None:
    # Drop indexes
    op.drop_index('idx_audit_events_action', table_name='audit_events')
    op.drop_index('idx_audit_events_created_at', table_name='audit_events')
    op.drop_index('idx_audit_events_resource', table_name='audit_events')
    op.drop_index('idx_audit_events_user_id', table_name='audit_events')
    # Drop table
    op.drop_table('audit_events')
