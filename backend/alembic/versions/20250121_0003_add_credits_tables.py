"""add credits system tables

Revision ID: 20250121_0003
Revises: 20250121_0002
Create Date: 2026-01-21

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '20250121_0003'
down_revision: Union[str, None] = '20250121_0002'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: None


def upgrade() -> None:
    # ============================================
    # 1. User credits table (one row per user)
    # ============================================
    op.create_table('user_credits',
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),

        # Credit balances
        sa.Column('image_credits', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('purchased_credits', sa.Integer(), nullable=False, server_default='0'),

        # Monthly reset tracking
        sa.Column('credits_used_this_month', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('monthly_credits', sa.Integer(), nullable=False, server_default='5'),

        sa.Column('last_monthly_reset', sa.Date(), nullable=True),

        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text('now()')),

        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('user_id')
    )

    op.create_index('idx_user_credits_balance', 'user_credits', ['user_id'])

    # ============================================
    # 2. Credit transactions (audit log)
    # ============================================
    op.create_table('credit_transactions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),

        sa.Column('amount', sa.Integer(), nullable=False),
        # Positive = add credits, Negative = use credits

        sa.Column('transaction_type', sa.String(length=50), nullable=False),
        # Types: monthly_refresh, purchase, usage, bonus, refund, admin_adjustment

        sa.Column('description', sa.TEXT(), nullable=False),
        sa.Column('meta_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True),

        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),

        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_index('idx_credit_transactions_user_date', 'credit_transactions',
                    ['user_id', sa.text('created_at DESC')])

    # Partial index for filtering by type
    op.create_index('idx_credit_transactions_type', 'credit_transactions',
                    ['user_id', 'transaction_type'],
                    postgresql_where=sa.text('transaction_type IN (\'usage\', \'purchase\')'))

    # ============================================
    # 3. Credit packages (for one-time purchases)
    # ============================================
    op.create_table('credit_packages',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('credits', sa.Integer(), nullable=False),
        sa.Column('price_usd', sa.Numeric(precision=10, scale=2), nullable=False),

        sa.Column('stripe_price_id', sa.String(length=255), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),

        sa.Column('display_order', sa.Integer(), nullable=False, server_default='0'),

        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),

        sa.PrimaryKeyConstraint('id')
    )

    op.create_index('idx_credit_packages_active', 'credit_packages',
                    ['is_active', 'display_order'])


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_table('credit_packages')
    op.drop_table('credit_transactions')
    op.drop_table('user_credits')
