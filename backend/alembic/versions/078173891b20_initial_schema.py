"""initial schema

Revision ID: 078173891b20
Revises:
Create Date: 2026-01-21 15:24:51.788081

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '078173891b20'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create citext extension
    op.execute('CREATE EXTENSION IF NOT EXISTS citext')

    # Users table (no dependencies)
    op.create_table('users',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('email', sa.String(length=255), nullable=False),
    sa.Column('password_hash', sa.String(length=255), nullable=True),
    sa.Column('name', sa.String(length=255), nullable=True),
    sa.Column('avatar_url', sa.TEXT(), nullable=True),
    sa.Column('provider', sa.String(length=20), nullable=False, server_default='email'),
    sa.Column('provider_id', sa.String(length=255), nullable=True),
    sa.Column('username', postgresql.CITEXT(), nullable=True),
    sa.Column('preferences', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='{}'),
    sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
    sa.CheckConstraint("username ~ '^[a-z0-9]([a-z0-9-]*[a-z0-9])?$'", name='username_format'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('email'),
    sa.UniqueConstraint('username')
    )

    # Projects table (without snapshot FKs first)
    op.create_table('projects',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('public_id', sa.String(length=8), nullable=True),
    sa.Column('slug', sa.String(length=100), nullable=True),
    sa.Column('name', sa.String(length=255), nullable=False),
    sa.Column('template_id', sa.String(length=50), nullable=True),
    sa.Column('template_inputs', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='{}'),
    sa.Column('status', sa.String(length=20), nullable=False, server_default='draft'),
    sa.Column('current_draft_id', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('published_snapshot_id', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('notification_email', sa.String(length=255), nullable=True),
    sa.Column('notification_enabled', sa.Boolean(), nullable=False, server_default='false'),
    sa.Column('published_at', sa.DateTime(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
    sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
    sa.CheckConstraint("slug ~ '^[a-z0-9]([a-z0-9-]*[a-z0-9])?$'", name='slug_format'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('public_id'),
    sa.UniqueConstraint('user_id', 'slug')
    )

    # Snapshots table (without project FK first)
    op.create_table('snapshots',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('project_id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('version_number', sa.Integer(), nullable=False),
    sa.Column('summary', sa.TEXT(), nullable=True),
    sa.Column('design_system', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='{}'),
    sa.Column('navigation', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='{}'),
    sa.Column('is_draft', sa.Boolean(), nullable=False, server_default='false'),
    sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('project_id', 'version_number'),
    postgresql.ExcludeConstraint((sa.column('project_id'), '='), (sa.column('is_draft'), '='),
                                  where=sa.text('is_draft = true'),
                                  using='btree',
                                  name='at_most_one_draft_per_project')
    )

    # Pages table
    op.create_table('pages',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('snapshot_id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('slug', sa.String(length=100), nullable=False),
    sa.Column('title', sa.String(length=255), nullable=False),
    sa.Column('html', sa.TEXT(), nullable=False),
    sa.Column('js', sa.TEXT(), nullable=True),
    sa.Column('page_metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='{}'),
    sa.Column('is_home', sa.Boolean(), nullable=False, server_default='false'),
    sa.Column('display_order', sa.Integer(), nullable=False, server_default='0'),
    sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
    sa.CheckConstraint("slug ~ '^[a-z0-9]([a-z0-9-]*[a-z0-9])?$'", name='slug_format'),
    sa.ForeignKeyConstraint(['snapshot_id'], ['snapshots.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('snapshot_id', 'slug')
    )

    # Create indexes
    op.create_index('uniq_home_per_snapshot', 'pages', ['snapshot_id'],
                    unique=True, postgresql_where=sa.text('is_home = true'))
    op.create_index('idx_snapshots_project_created', 'snapshots', ['project_id', 'created_at'])
    op.create_index('idx_pages_snapshot_order', 'pages', ['snapshot_id', 'display_order'])
    op.create_index('idx_projects_user_updated', 'projects', ['user_id', 'updated_at'])
    op.create_index('idx_projects_public_id', 'projects', ['public_id'],
                    postgresql_where=sa.text('public_id IS NOT NULL'))

    # Add circular FKs after tables exist (use batch_alter_table)
    with op.batch_alter_table('projects') as batch_op:
        batch_op.create_foreign_key('fk_projects_current_draft', 'snapshots', ['current_draft_id'], ['id'])
        batch_op.create_foreign_key('fk_projects_published_snapshot', 'snapshots', ['published_snapshot_id'], ['id'])

    with op.batch_alter_table('snapshots') as batch_op:
        batch_op.create_foreign_key('fk_snapshots_project', 'projects', ['project_id'], ['id'], ondelete='CASCADE')


def downgrade() -> None:
    # Drop circular FKs first
    with op.batch_alter_table('snapshots') as batch_op:
        batch_op.drop_constraint('fk_snapshots_project', type_='foreignkey')

    with op.batch_alter_table('projects') as batch_op:
        batch_op.drop_constraint('fk_projects_current_draft', type_='foreignkey')
        batch_op.drop_constraint('fk_projects_published_snapshot', type_='foreignkey')

    # Drop indexes
    op.drop_index('idx_projects_public_id', table_name='projects')
    op.drop_index('idx_projects_user_updated', table_name='projects')
    op.drop_index('idx_pages_snapshot_order', table_name='pages')
    op.drop_index('idx_snapshots_project_created', table_name='snapshots')
    op.drop_index('uniq_home_per_snapshot', table_name='pages')

    # Drop tables
    op.drop_table('pages')
    op.drop_table('snapshots')
    op.drop_table('projects')
    op.drop_table('users')

    op.execute('DROP EXTENSION IF EXISTS citext')
