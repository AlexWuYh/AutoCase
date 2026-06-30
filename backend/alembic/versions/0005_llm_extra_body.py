"""add extra_body to llm_configs

Revision ID: 0005_llm_extra_body
Revises: 0004_generation_jobs
Create Date: 2026-06-30
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0005_llm_extra_body"
down_revision: Union[str, None] = "0004_generation_jobs"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("llm_configs", sa.Column("extra_body", sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column("llm_configs", "extra_body")
