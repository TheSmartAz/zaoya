"""Add custom_domains table for custom domain support.

Revision ID: 20260122_0007
Revises: 20260121_0006
Create Date: 2026-01-22 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '20260122_0007'
down_revision: Union[str, None] = '20260121_0006'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create custom_domains table
    op.create_table(
        'custom_domains',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), nullable=False),
        # Domain info
        sa.Column('domain', sa.String(255), nullable=False),
        sa.Column('is_apex', sa.Boolean(), nullable=False, server_default='false'),
        # Verification
        sa.Column('verification_token', sa.String(64), nullable=False),
        sa.Column('verification_status', sa.String(20), nullable=False, server_default='pending'),
        sa.Column('verified_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('verification_expires_at', sa.DateTime(timezone=True), nullable=False),
        # SSL status
        sa.Column('ssl_status', sa.String(20), nullable=False, server_default='pending'),
        sa.Column('ssl_provisioned_at', sa.DateTime(timezone=True), nullable=True),
        # Operational fields
        sa.Column('last_checked_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('attempt_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('failure_reason', sa.String(255), nullable=True),
        # Timestamps
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        # Primary key
        sa.PrimaryKeyConstraint('id'),
        # Foreign key to projects (CASCADE on delete)
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        # Unique constraints
        sa.UniqueConstraint('domain', name='uq_custom_domains_domain'),
        sa.UniqueConstraint('project_id', name='uq_custom_domains_project_id'),  # Enforces 1:1 mapping
        # Check constraints
        sa.CheckConstraint(
            "verification_status IN ('pending', 'verified', 'failed', 'active')",
            name='valid_verification_status'
        ),
        sa.CheckConstraint(
            "ssl_status IN ('pending', 'provisioning', 'active', 'error')",
            name='valid_ssl_status'
        ),
    )

    # Create indexes
    op.create_index('idx_custom_domains_domain', 'custom_domains', ['domain'])
    op.create_index('idx_custom_domains_verification_status', 'custom_domains', ['verification_status'])
    op.create_index(
        'idx_custom_domains_pending_verification',
        'custom_domains',
        ['verification_expires_at'],
        postgresql_where=sa.text("verification_status = 'pending'")
    )


def downgrade() -> None:
    # Drop indexes
    op.drop_index('idx_custom_domains_pending_verification', table_name='custom_domains')
    op.drop_index('idx_custom_domains_verification_status', table_name='custom_domains')
    op.drop_index('idx_custom_domains_domain', table_name='custom_domains')
    # Drop table
    op.drop_table('custom_domains')
