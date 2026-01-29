"""add subscription tables (mock for v1)

Revision ID: 20250121_0005
Revises: 20250121_0004
Create Date: 2026-01-21

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '20250121_0005'
down_revision: Union[str, None] = '20250121_0004'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: None


def upgrade() -> None:
    # ============================================
    # 1. Subscription plans
    # ============================================
    op.create_table('subscription_plans',
        sa.Column('id', sa.String(length=50), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.TEXT(), nullable=True),

        # Pricing
        sa.Column('price_monthly_usd', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('price_yearly_usd', sa.Numeric(precision=10, scale=2), nullable=False),

        # Stripe integration (optional for now)
        sa.Column('stripe_price_id_monthly', sa.String(length=255), nullable=True),
        sa.Column('stripe_price_id_yearly', sa.String(length=255), nullable=True),

        # Feature limits
        sa.Column('limits', postgresql.JSONB(astext_type=sa.Text()), nullable=False),

        # Features list for display
        sa.Column('features', postgresql.ARRAY(sa.String(length=200)), nullable=True),

        sa.Column('display_order', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),

        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),

        sa.PrimaryKeyConstraint('id')
    )

    # Seed initial plans
    op.execute("""
        INSERT INTO subscription_plans (id, name, price_monthly_usd, price_yearly_usd, limits, features, display_order, is_active) VALUES
        ('free', 'Free', 0.00, 0.00, '{"projects": 3, "pages_per_project": 1, "image_credits": 5, "custom_domain": false, "analytics_retention_days": 7, "ab_testing": false, "advanced_analytics": false, "team_seats": 1}'::jsonb, ARRAY['3 projects', '1 page per project', 'Basic analytics', '5 image credits'], 1, true),
        ('pro', 'Pro', 12.00, 120.00, '{"projects": -1, "pages_per_project": -1, "image_credits": 50, "custom_domain": true, "analytics_retention_days": 365, "ab_testing": true, "advanced_analytics": true, "team_seats": 1}'::jsonb, ARRAY['Unlimited projects', 'Unlimited pages', 'Advanced analytics', 'A/B testing', 'Custom domain', '50 image credits/mo'], 2, true),
        ('team', 'Team', 29.00, 290.00, '{"projects": -1, "pages_per_project": -1, "image_credits": 200, "custom_domain": true, "analytics_retention_days": 365, "ab_testing": true, "advanced_analytics": true, "team_seats": 5}'::jsonb, ARRAY['Everything in Pro', '5 team seats', 'Collaboration workflows', '200 image credits/mo'], 3, false)
    """)

    op.create_index('idx_plans_active_display', 'subscription_plans',
                    ['is_active', 'display_order'])

    # ============================================
    # 2. User subscriptions
    # ============================================
    op.create_table('user_subscriptions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),

        sa.Column('plan_id', sa.String(length=50), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='active'),

        # Stripe integration (optional for now)
        sa.Column('stripe_customer_id', sa.String(length=255), nullable=True),
        sa.Column('stripe_subscription_id', sa.String(length=255), nullable=True),

        # Billing cycle
        sa.Column('billing_interval', sa.String(length=10), nullable=False),

        sa.Column('current_period_start', sa.DateTime(timezone=True), nullable=True),
        sa.Column('current_period_end', sa.DateTime(timezone=True), nullable=True),

        # Trial (if applicable)
        sa.Column('trial_start', sa.DateTime(timezone=True), nullable=True),
        sa.Column('trial_end', sa.DateTime(timezone=True), nullable=True),

        # Cancellation
        sa.Column('cancel_at_period_end', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('canceled_at', sa.DateTime(timezone=True), nullable=True),

        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text('now()')),

        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['plan_id'], ['subscription_plans.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id')
    )

    op.create_index('idx_subscriptions_user', 'user_subscriptions', ['user_id'])
    op.create_index('idx_subscriptions_status', 'user_subscriptions',
                    ['status', sa.text('current_period_end')])

    op.create_index('idx_subscriptions_stripe', 'user_subscriptions',
                    ['stripe_subscription_id'],
                    postgresql_where=sa.text('stripe_subscription_id IS NOT NULL'))

    # ============================================
    # 3. Subscription events (webhook log)
    # ============================================
    op.create_table('subscription_events',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('subscription_id', sa.String(length=255), nullable=True),

        sa.Column('event_type', sa.String(length=100), nullable=False),

        sa.Column('stripe_event_id', sa.String(length=255), nullable=True),
        sa.Column('event_data', postgresql.JSONB(astext_type=sa.Text()), nullable=False),

        sa.Column('processed', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('processing_error', sa.TEXT(), nullable=True),

        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),

        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('stripe_event_id')
    )

    op.create_index('idx_subscription_events_user', 'subscription_events',
                    ['user_id', sa.text('created_at DESC')])

    op.create_index('idx_subscription_events_unprocessed', 'subscription_events',
                    ['processed', sa.text('created_at')],
                    postgresql_where=sa.text('processed = false'))


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_table('subscription_events')
    op.drop_table('user_subscriptions')
    op.drop_table('subscription_plans')
