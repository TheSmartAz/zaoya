"""add analytics tables

Revision ID: 20250121_0001
Revises: 078173891b20
Create Date: 2026-01-21

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '20250121_0001'
down_revision: Union[str, None] = '078173891b20'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: None


def upgrade() -> None:
    # Create extensions for advanced analytics
    op.execute('CREATE EXTENSION IF NOT EXISTS btree_gin')
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM pg_available_extensions WHERE name = 'brin') THEN
                CREATE EXTENSION IF NOT EXISTS brin;
            END IF;
        END $$;
        """
    )

    # ============================================
    # 1. Raw events table (time-series optimized)
    # ============================================
    op.create_table('analytics_events',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('visitor_id', sa.String(length=64), nullable=False),
        sa.Column('session_id', sa.String(length=64), nullable=True),
        sa.Column('event_type', sa.String(length=50), nullable=False),
        sa.Column('event_name', sa.String(length=100), nullable=True),
        sa.Column('properties', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='{}'),

        # Context metadata
        sa.Column('referrer', sa.TEXT(), nullable=True),
        sa.Column('utm_source', sa.String(length=100), nullable=True),
        sa.Column('utm_medium', sa.String(length=100), nullable=True),
        sa.Column('utm_campaign', sa.String(length=100), nullable=True),
        sa.Column('device_type', sa.String(length=20), nullable=False, server_default='desktop'),
        sa.Column('browser', sa.String(length=50), nullable=True),
        sa.Column('country', sa.String(length=2), nullable=True),
        sa.Column('city', sa.String(length=100), nullable=True),

        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),

        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # Indexes for analytics_events
    op.create_index('idx_events_project_timestamp', 'analytics_events',
                    ['project_id', sa.text('timestamp DESC')])

    # BRIN index for timestamp (efficient for large time-series data)
    op.create_index('idx_events_timestamp_brin', 'analytics_events',
                    ['timestamp'], postgresql_using='brin')

    # GIN index for JSONB properties filtering
    op.create_index('idx_events_properties', 'analytics_events',
                    ['properties'], postgresql_using='gin')

    # Session-based query optimization
    op.create_index('idx_events_session', 'analytics_events',
                    ['session_id', sa.text('timestamp DESC')])

    # Funnel analysis queries
    op.create_index('idx_events_project_type', 'analytics_events',
                    ['project_id', 'event_type', 'timestamp'])

    # ============================================
    # 2. Sessions table (aggregated visitor sessions)
    # ============================================
    op.create_table('analytics_sessions',
        sa.Column('id', sa.String(length=64), nullable=False),
        sa.Column('visitor_id', sa.String(length=64), nullable=False),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), nullable=False),

        sa.Column('started_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('ended_at', sa.DateTime(timezone=True), nullable=True),

        sa.Column('page_views', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('events', sa.Integer(), nullable=False, server_default='0'),

        sa.Column('entry_page', sa.String(length=100), nullable=True),
        sa.Column('exit_page', sa.String(length=100), nullable=True),
        sa.Column('duration_seconds', sa.Integer(), nullable=True),

        sa.Column('device_type', sa.String(length=20), nullable=False, server_default='desktop'),
        sa.Column('browser', sa.String(length=50), nullable=True),
        sa.Column('country', sa.String(length=2), nullable=True),

        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # Indexes for analytics_sessions
    op.create_index('idx_sessions_visitor_project', 'analytics_sessions',
                    ['visitor_id', 'project_id', sa.text('started_at DESC')])
    op.create_index('idx_sessions_project_started', 'analytics_sessions',
                    ['project_id', sa.text('started_at DESC')])

    # ============================================
    # 3. Daily aggregation table (pre-computed stats)
    # ============================================
    op.create_table('analytics_daily',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),

        # Daily metrics
        sa.Column('views', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('unique_visitors', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('sessions', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('cta_clicks', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('form_submissions', sa.Integer(), nullable=False, server_default='0'),

        # Engagement metrics
        sa.Column('avg_session_duration', sa.Integer(), nullable=True),
        sa.Column('bounce_rate', sa.Numeric(precision=5, scale=2), nullable=True),

        # Device breakdown
        sa.Column('device_counts', postgresql.JSONB(astext_type=sa.Text())),
        sa.Column('top_pages', postgresql.JSONB(astext_type=sa.Text())),
        sa.Column('traffic_sources', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='{}'),

        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text('now()')),

        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('project_id', 'date')
    )

    # Indexes for analytics_daily
    op.create_index('idx_daily_project_date', 'analytics_daily',
                    ['project_id', sa.text('date DESC')])

    # Partial index for recent data (skip here; CURRENT_DATE is not immutable)

    # ============================================
    # 4. Funnels table (user-defined conversion funnels)
    # ============================================
    op.create_table('analytics_funnels',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('steps', postgresql.JSONB(astext_type=sa.Text()), nullable=False),

        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),

        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_index('idx_funnels_project', 'analytics_funnels', ['project_id'])

    # ============================================
    # 5. Cohorts table (for retention analysis)
    # ============================================
    op.create_table('analytics_cohorts',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('cohort_type', sa.String(length=50), nullable=False),
        sa.Column('cohort_date', sa.Date(), nullable=False),
        sa.Column('cohort_label', sa.String(length=100), nullable=False),

        sa.Column('initial_size', sa.Integer(), nullable=False),
        sa.Column('period_data', postgresql.JSONB(astext_type=sa.Text()), nullable=False),

        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),

        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_index('idx_cohorts_project_date', 'analytics_cohorts',
                    ['project_id', sa.text('cohort_date DESC')])


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_table('analytics_cohorts')
    op.drop_table('analytics_funnels')
    op.drop_table('analytics_daily')
    op.drop_table('analytics_sessions')
    op.drop_table('analytics_events')

    op.execute('DROP EXTENSION IF EXISTS brin')
    op.execute('DROP EXTENSION IF EXISTS btree_gin')
