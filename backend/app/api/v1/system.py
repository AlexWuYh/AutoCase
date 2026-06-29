"""System-level health and info endpoints."""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ...database import get_db
from ...deps import get_current_user
from ...models.job import GenerationJob
from ...models.llm_config import LLMConfig
from ...models.prompt import SystemPrompt
from ...models.requirement_group import RequirementGroup
from ...models.user import User

router = APIRouter()


@router.get("/stats", tags=["system"])
def get_stats(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    """Return dashboard statistics for the current user."""
    is_admin = current_user.role == "admin"

    groups_q = select(func.count(RequirementGroup.id))
    if not is_admin:
        groups_q = groups_q.where(RequirementGroup.owner_id == current_user.id)
    group_count = db.execute(groups_q).scalar_one()

    jobs_q = select(func.count(GenerationJob.id))
    if not is_admin:
        jobs_q = jobs_q.where(GenerationJob.user_id == current_user.id)
    job_count = db.execute(jobs_q).scalar_one()

    result = {
        "requirement_groups": group_count,
        "generation_jobs": job_count,
    }
    if is_admin:
        result["users"] = db.execute(select(func.count(User.id))).scalar_one()
        result["llm_configs"] = db.execute(select(func.count(LLMConfig.id))).scalar_one()
        result["system_prompts"] = db.execute(select(func.count(SystemPrompt.id))).scalar_one()
    return result
