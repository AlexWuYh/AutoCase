"""api_keys table

Revision ID: 0006_api_keys
Revises: 0005_llm_extra_body
Create Date: 2026-07-01
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0006_api_keys"
down_revision: Union[str, None] = "0005_llm_extra_body"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "api_keys",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(128), nullable=False, server_default=""),
        sa.Column("key_hash", sa.String(64), nullable=False),
        sa.Column("prefix", sa.String(16), nullable=False),
        sa.Column("owner_id", sa.Integer(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("1")),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("last_used_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["owner_id"], ["users.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_api_keys_owner_id", "api_keys", ["owner_id"])
    op.create_index("ix_api_keys_key_hash", "api_keys", ["key_hash"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_api_keys_key_hash", table_name="api_keys")
    op.drop_index("ix_api_keys_owner_id", table_name="api_keys")
    op.drop_table("api_keys")
