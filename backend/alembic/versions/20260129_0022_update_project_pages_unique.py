"""Update project_pages unique constraint to include branch_id.

Revision ID: 20260129_0022
Revises: 20260129_0021
Create Date: 2026-01-29
"""

from alembic import op

revision = "20260129_0022"
down_revision = "20260129_0021"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_constraint("uq_project_pages_project_id_path", "project_pages", type_="unique")
    op.create_unique_constraint(
        "uq_project_pages_project_branch_path",
        "project_pages",
        ["project_id", "branch_id", "path"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "uq_project_pages_project_branch_path",
        "project_pages",
        type_="unique",
    )
    op.create_unique_constraint(
        "uq_project_pages_project_id_path",
        "project_pages",
        ["project_id", "path"],
    )
