"""llm_configs and system_prompts tables

Revision ID: 0003_llm_config_prompt
Revises: 0002_requirements
Create Date: 2026-06-29
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0003_llm_config_prompt"
down_revision: Union[str, None] = "0002_requirements"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "llm_configs",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("provider", sa.String(32), nullable=False, server_default="openai"),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.text("1")),
        sa.Column("api_key_env", sa.String(128), nullable=True),
        sa.Column("allow_empty_key", sa.Boolean(), nullable=False, server_default=sa.text("0")),
        sa.Column("base_url", sa.String(512), nullable=True),
        sa.Column("api_mode", sa.String(32), nullable=False, server_default="chat_completions"),
        sa.Column("model", sa.String(128), nullable=False, server_default="gpt-4o-mini"),
        sa.Column("temperature", sa.Float(), nullable=False, server_default="0.2"),
        sa.Column("max_tokens", sa.Integer(), nullable=False, server_default="2000"),
        sa.Column("top_p", sa.Float(), nullable=False, server_default="1.0"),
        sa.Column("frequency_penalty", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("presence_penalty", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("retry_count", sa.Integer(), nullable=False, server_default="2"),
        sa.Column("debug_log", sa.Boolean(), nullable=False, server_default=sa.text("0")),
        sa.Column("is_default", sa.Boolean(), nullable=False, server_default=sa.text("0")),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now()),
    )

    op.create_table(
        "system_prompts",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("content", sa.Text(), nullable=False, server_default=""),
        sa.Column("description", sa.String(512), nullable=True),
        sa.Column("is_default", sa.Boolean(), nullable=False, server_default=sa.text("0")),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("system_prompts")
    op.drop_table("llm_configs")
