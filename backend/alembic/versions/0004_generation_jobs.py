"""generation_jobs and generated_cases tables

Revision ID: 0004_generation_jobs
Revises: 0003_llm_config_prompt
Create Date: 2026-06-29
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0004_generation_jobs"
down_revision: Union[str, None] = "0003_llm_config_prompt"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "generation_jobs",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("group_id", sa.Integer(), nullable=True),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("llm_config_id", sa.Integer(), nullable=True),
        sa.Column("prompt_id", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(16), nullable=False, server_default="pending"),
        sa.Column("total", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("finished", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("started_at", sa.DateTime(), nullable=True),
        sa.Column("finished_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["group_id"], ["requirement_groups.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["llm_config_id"], ["llm_configs.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["prompt_id"], ["system_prompts.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_jobs_group_id", "generation_jobs", ["group_id"])
    op.create_index("ix_jobs_user_id", "generation_jobs", ["user_id"])
    op.create_index("ix_jobs_status", "generation_jobs", ["status"])

    op.create_table(
        "generated_cases",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("job_id", sa.Integer(), nullable=False),
        sa.Column("case_id", sa.String(32), nullable=False),
        sa.Column("module", sa.String(256), nullable=False),
        sa.Column("case_type", sa.String(128), nullable=False, server_default=""),
        sa.Column("name", sa.String(512), nullable=False, server_default=""),
        sa.Column("priority", sa.String(8), nullable=False, server_default="2"),
        sa.Column("preconditions", sa.Text(), nullable=False, server_default=""),
        sa.Column("steps", sa.JSON(), nullable=False),
        sa.Column("expected", sa.JSON(), nullable=False),
        sa.Column("keywords", sa.String(1024), nullable=False, server_default=""),
        sa.Column("stage", sa.String(64), nullable=False, server_default="功能测试阶段"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["job_id"], ["generation_jobs.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_cases_job_id", "generated_cases", ["job_id"])


def downgrade() -> None:
    op.drop_index("ix_cases_job_id", table_name="generated_cases")
    op.drop_table("generated_cases")
    op.drop_index("ix_jobs_status", table_name="generation_jobs")
    op.drop_index("ix_jobs_user_id", table_name="generation_jobs")
    op.drop_index("ix_jobs_group_id", table_name="generation_jobs")
    op.drop_table("generation_jobs")
