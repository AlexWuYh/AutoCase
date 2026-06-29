"""Pydantic schemas for generation jobs and generated test cases."""
from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict


# ─── Test Case ──────────────────────────────────────────────────────────

class GeneratedCaseOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    job_id: int
    case_id: str
    module: str
    case_type: str
    name: str
    priority: str
    preconditions: str
    steps: List[str]
    expected: List[str]
    keywords: str
    stage: str
    created_at: datetime


# ─── Job ────────────────────────────────────────────────────────────────

class JobCreate(BaseModel):
    group_id: int
    llm_config_id: Optional[int] = None
    prompt_id: Optional[int] = None


class JobOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    group_id: int | None
    user_id: int | None
    status: str
    total: int
    finished: int
    percent: float = 0.0
    error: Optional[str] = None
    group_name: Optional[str] = None
    user_name: Optional[str] = None
    llm_config_name: Optional[str] = None
    prompt_name: Optional[str] = None
    created_at: datetime
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
