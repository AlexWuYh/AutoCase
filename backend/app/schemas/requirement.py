"""Pydantic schemas for requirement groups and requirements."""
from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


# ─── Group ──────────────────────────────────────────────────────────────

class GroupBase(BaseModel):
    name: str = Field(min_length=1, max_length=128)
    description: Optional[str] = Field(default=None, max_length=2000)


class GroupCreate(GroupBase):
    pass


class GroupUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=128)
    description: Optional[str] = Field(default=None, max_length=2000)


class GroupOut(GroupBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    owner_id: int
    owner_username: Optional[str] = None
    requirement_count: int = 0
    created_at: datetime
    updated_at: datetime


# ─── Requirement ────────────────────────────────────────────────────────

class RequirementBase(BaseModel):
    module: str = Field(min_length=1, max_length=256)
    feature: str = Field(min_length=1, max_length=256)
    description: str = Field(default="", max_length=4000)
    keywords: List[str] = Field(default_factory=list)


class RequirementCreate(RequirementBase):
    pass


class RequirementUpdate(BaseModel):
    module: Optional[str] = Field(default=None, min_length=1, max_length=256)
    feature: Optional[str] = Field(default=None, min_length=1, max_length=256)
    description: Optional[str] = Field(default=None, max_length=4000)
    keywords: Optional[List[str]] = None


class RequirementOut(RequirementBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    group_id: int
    sort_order: int
    created_at: datetime
    updated_at: datetime


class RequirementBatchCreate(BaseModel):
    """Batch create: replace or append a list of requirements to a group."""

    items: List[RequirementCreate]
    mode: str = Field(default="append", pattern="^(append|replace)$")


# ─── Import result ──────────────────────────────────────────────────────

class ImportResult(BaseModel):
    imported: int
    skipped: int
    total_in_file: int
