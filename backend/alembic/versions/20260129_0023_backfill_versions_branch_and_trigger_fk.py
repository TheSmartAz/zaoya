"""Backfill version branches and add trigger message FK.

Revision ID: 20260129_0023
Revises: 20260129_0022
Create Date: 2026-01-29
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "20260129_0023"
down_revision: Union[str, None] = "20260129_0022"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    bind.execute(
        sa.text(
            """
            UPDATE versions v
            SET branch_id = p.active_branch_id
            FROM projects p
            WHERE v.project_id = p.id
              AND v.branch_id IS NULL
              AND p.active_branch_id IS NOT NULL
            """
        )
    )
    bind.execute(
        sa.text(
            """
            UPDATE versions v
            SET branch_id = b.id
            FROM branches b
            WHERE v.project_id = b.project_id
              AND b.is_default = true
              AND v.branch_id IS NULL
            """
        )
    )
    bind.execute(
        sa.text(
            """
            UPDATE versions v
            SET branch_label = COALESCE(b.label, b.name)
            FROM branches b
            WHERE v.branch_id = b.id
              AND (v.branch_label IS NULL OR v.branch_label = '')
            """
        )
    )
    bind.execute(
        sa.text(
            """
            UPDATE versions
            SET trigger_message_id = NULL
            WHERE trigger_message_id IS NOT NULL
              AND trigger_message_id NOT IN (SELECT id FROM chat_messages)
            """
        )
    )
    op.create_foreign_key(
        "fk_versions_trigger_message_id_chat_messages",
        "versions",
        "chat_messages",
        ["trigger_message_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint(
        "fk_versions_trigger_message_id_chat_messages",
        "versions",
        type_="foreignkey",
    )
