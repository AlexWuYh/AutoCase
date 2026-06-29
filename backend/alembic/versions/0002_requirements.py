"""requirement groups and requirements tables

Revision ID: 0002_requirements
Revises: 0001_initial
Create Date: 2026-06-29

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0002_requirements"
down_revision: Union[str, None] = "0001_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "requirement_groups",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("owner_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.ForeignKeyConstraint(
            ["owner_id"], ["users.id"], ondelete="CASCADE", name="fk_requirement_groups_owner"
        ),
    )
    op.create_index(
        "ix_requirement_groups_owner_id", "requirement_groups", ["owner_id"]
    )

    op.create_table(
        "requirements",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("group_id", sa.Integer(), nullable=False),
        sa.Column("module", sa.String(length=256), nullable=False),
        sa.Column("feature", sa.String(length=256), nullable=False),
        sa.Column("description", sa.Text(), nullable=False, server_default=""),
        sa.Column("keywords", sa.JSON(), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.ForeignKeyConstraint(
            ["group_id"],
            ["requirement_groups.id"],
            ondelete="CASCADE",
            name="fk_requirements_group",
        ),
    )
    op.create_index("ix_requirements_group_id", "requirements", ["group_id"])
    op.create_index(
        "ix_requirements_sort_order", "requirements", ["group_id", "sort_order"]
    )


def downgrade() -> None:
    op.drop_index("ix_requirements_sort_order", table_name="requirements")
    op.drop_index("ix_requirements_group_id", table_name="requirements")
    op.drop_table("requirements")
    op.drop_index("ix_requirement_groups_owner_id", table_name="requirement_groups")
    op.drop_table("requirement_groups")
