"""Open API schemas (third-party generation)."""
from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field


class OpenCaseInput(BaseModel):
    module: str = Field(min_length=1, max_length=256)
    feature: str = Field(default="", max_length=256)
    description: str = Field(default="", max_length=4000)
    keywords: List[str] = Field(default_factory=list)


class OpenGenerateRequest(BaseModel):
    """Provide either `text` (YAML string, CLI-compatible) or `cases` (list)."""

    text: Optional[str] = Field(default=None, description="YAML 文本，与 CLI 输入格式一致")
    cases: Optional[List[OpenCaseInput]] = Field(default=None, description="结构化需求点数组")
    llm_config_id: Optional[int] = None
    prompt_id: Optional[int] = None
    group_name: Optional[str] = Field(default=None, max_length=128)


class OpenCaseOut(BaseModel):
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


class OpenGenerateResult(BaseModel):
    job_id: int
    group_id: int
    status: str
    total: int
    finished: int
    cases: List[OpenCaseOut] = Field(default_factory=list)
    error: Optional[str] = None


class OpenJobStatus(BaseModel):
    job_id: int
    group_id: int | None
    status: str
    total: int
    finished: int
    percent: float
    error: Optional[str] = None
    cases: List[OpenCaseOut] = Field(default_factory=list)
