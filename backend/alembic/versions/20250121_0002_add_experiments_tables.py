"""add experiments and A/B testing tables

Revision ID: 20250121_0002
Revises: 20250121_0001
Create Date: 2026-01-21

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '20250121_0002'
down_revision: Union[str, None] = '20250121_0001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: None


def upgrade() -> None:
    # ============================================
    # 1. Experiments table
    # ============================================
    op.create_table('experiments',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='draft'),

        # Traffic configuration
        sa.Column('traffic_split', postgresql.JSONB(astext_type=sa.Text()), nullable=False),

        # Conversion goal
        sa.Column('conversion_goal', postgresql.JSONB(astext_type=sa.Text()), nullable=False),

        sa.Column('start_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('end_date', sa.DateTime(timezone=True), nullable=True),

        sa.Column('winner_variant_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('winner_confidence', sa.Numeric(precision=5, scale=2), nullable=True),

        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=False),

        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # Indexes for experiments
    op.create_index('idx_experiments_project_status', 'experiments',
                    ['project_id', 'status'])
    op.create_index('idx_experiments_status_dates', 'experiments',
                    ['status', 'start_date', sa.text('end_date DESC NULLS LAST')])

    # ============================================
    # 2. Experiment variants table
    # ============================================
    op.create_table('experiment_variants',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('experiment_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('is_control', sa.Boolean(), nullable=False, server_default='false'),

        # Page content (can be entire snapshot or partial)
        sa.Column('snapshot_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('page_content', postgresql.JSONB(astext_type=sa.Text()), nullable=True),

        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),

        sa.ForeignKeyConstraint(['experiment_id'], ['experiments.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['snapshot_id'], ['snapshots.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )

    # Ensure each experiment has exactly one control variant
    op.create_index('uniq_control_per_experiment', 'experiment_variants',
                    ['experiment_id'],
                    unique=True,
                    postgresql_where=sa.text('is_control = true'))

    op.create_index('idx_variants_experiment', 'experiment_variants',
                    ['experiment_id', sa.text('is_control DESC')])

    # ============================================
    # 3. Experiment results table (aggregated statistics)
    # ============================================
    op.create_table('experiment_results',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('experiment_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('variant_id', postgresql.UUID(as_uuid=True), nullable=False),

        # Metrics
        sa.Column('visitors', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('conversions', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('conversion_rate', sa.Numeric(precision=5, scale=2), nullable=True),

        # Statistical analysis
        sa.Column('confidence_level', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('is_significant', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('p_value', sa.Numeric(precision=10, scale=8), nullable=True),

        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text('now()')),

        sa.ForeignKeyConstraint(['experiment_id'], ['experiments.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['variant_id'], ['experiment_variants.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('experiment_id', 'variant_id')
    )

    op.create_index('idx_results_experiment_variant', 'experiment_results',
                    ['experiment_id', 'variant_id'])

    # ============================================
    # 4. Experiment assignments (visitor-to-variant mapping)
    # ============================================
    op.create_table('experiment_assignments',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('experiment_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('variant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('visitor_id', sa.String(length=64), nullable=False),

        sa.Column('assigned_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),

        sa.ForeignKeyConstraint(['experiment_id'], ['experiments.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['variant_id'], ['experiment_variants.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # Index for deterministic assignment lookup
    op.create_index('idx_assignments_experiment_visitor', 'experiment_assignments',
                    ['experiment_id', 'visitor_id'])

    # Unique constraint: one visitor can only be assigned to one variant per experiment
    op.create_index('uniq_assignment', 'experiment_assignments',
                    ['experiment_id', 'visitor_id'],
                    unique=True)

    # ============================================
    # 5. Experiment conversions (individual conversion events)
    # ============================================
    op.create_table('experiment_conversions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('experiment_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('variant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('visitor_id', sa.String(length=64), nullable=False),

        sa.Column('goal_type', sa.String(length=50), nullable=False),
        sa.Column('goal_metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),

        sa.Column('converted_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),

        sa.ForeignKeyConstraint(['experiment_id'], ['experiments.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['variant_id'], ['experiment_variants.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_index('idx_conversions_experiment_variant', 'experiment_conversions',
                    ['experiment_id', 'variant_id', sa.text('converted_at DESC')])

    # Unique constraint: one visitor can only convert once per variant
    op.create_index('uniq_conversion', 'experiment_conversions',
                    ['experiment_id', 'variant_id', 'visitor_id'],
                    unique=True)

    # ============================================
    # 6. Experiment audit log (for status changes)
    # ============================================
    op.create_table('experiment_audit_log',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('experiment_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('action', sa.String(length=50), nullable=False),

        sa.Column('old_status', sa.String(length=20), nullable=True),
        sa.Column('new_status', sa.String(length=20), nullable=True),
        sa.Column('audit_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True),

        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=False),

        sa.ForeignKeyConstraint(['experiment_id'], ['experiments.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_index('idx_audit_log_experiment', 'experiment_audit_log',
                    ['experiment_id', sa.text('created_at DESC')])


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_table('experiment_audit_log')
    op.drop_table('experiment_conversions')
    op.drop_table('experiment_assignments')
    op.drop_table('experiment_results')
    op.drop_table('experiment_variants')
    op.drop_table('experiments')
