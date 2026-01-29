"""add asset library table

Revision ID: 20250121_0004
Revises: 20250121_0003
Create Date: 2026-01-21

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '20250121_0004'
down_revision: Union[str, None] = '20250121_0003'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: None


def upgrade() -> None:
    # ============================================
    # 1. Assets table (images)
    # ============================================
    op.create_table('assets',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), nullable=True),

        sa.Column('asset_type', sa.String(length=20), nullable=False),
        # Types: generated, uploaded

        sa.Column('url', sa.TEXT(), nullable=False),
        sa.Column('thumbnail_url', sa.TEXT(), nullable=True),
        sa.Column('original_filename', sa.String(length=255), nullable=True),

        # For generated images
        sa.Column('prompt', sa.TEXT(), nullable=True),
        sa.Column('generation_provider', sa.String(length=50), nullable=True),
        sa.Column('generation_metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),

        # File metadata
        sa.Column('file_size_bytes', sa.Integer(), nullable=True),
        sa.Column('mime_type', sa.String(length=100), nullable=True),
        sa.Column('width', sa.Integer(), nullable=True),
        sa.Column('height', sa.Integer(), nullable=True),

        # Organization
        sa.Column('tags', postgresql.ARRAY(sa.String(length=50)), nullable=True),
        sa.Column('alt_text', sa.TEXT(), nullable=True),

        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),

        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )

    # Indexes for asset library queries
    op.create_index('idx_assets_user_created', 'assets',
                    ['user_id', sa.text('created_at DESC')])

    # Project-specific assets
    op.create_index('idx_assets_project', 'assets',
                    ['project_id', sa.text('created_at DESC')])

    # Search by tags
    op.create_index('idx_assets_tags', 'assets',
                    ['tags'], postgresql_using='gin')

    # Filter by type
    op.create_index('idx_assets_user_type', 'assets',
                    ['user_id', 'asset_type'])

    # Combined GIN index for metadata search
    op.create_index('idx_assets_metadata', 'assets',
                    ['generation_metadata'], postgresql_using='gin')


def downgrade() -> None:
    op.drop_table('assets')
