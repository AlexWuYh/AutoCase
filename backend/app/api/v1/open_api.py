"""Open API — third-party test-case generation via X-API-Key.

Designed for headless callers (Feishu/WeChat bots, scripts). Accepts either a
YAML text body, a structured cases array, or a YAML file upload. Cases are
persisted (a throwaway requirement group + a generation job) so results are
visible/exportable in the web UI afterwards.
"""
from __future__ import annotations

import time
from typing import Annotated, List, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from ...config import get_settings
from ...database import get_db
from ...deps import get_api_key_user
from ...models.case import GeneratedCase
from ...models.job import GenerationJob
from ...models.requirement import Requirement
from ...models.requirement_group import RequirementGroup
from ...models.user import User
from ...schemas.open_api import (
    OpenCaseInput,
    OpenCaseOut,
    OpenGenerateRequest,
    OpenGenerateResult,
    OpenJobStatus,
)
from ...services.generation_service import run_generation
from ...services.yaml_service import parse_yaml_to_specs
from ...tasks.generation import generate_job

router = APIRouter()
settings = get_settings()

# Synchronous generation blocks the request; cap the number of requirement
# points to keep latency sane. Larger batches must use the async endpoint.
SYNC_MAX_ITEMS = 20


def _specs_from_request(text: Optional[str], cases: Optional[List[OpenCaseInput]]) -> List[dict]:
    """Normalize either YAML text or a structured cases array into dict specs."""
    if text and cases:
        raise HTTPException(status_code=400, detail="text 和 cases 只能提供其一")
    if text:
        try:
            specs = parse_yaml_to_specs(text)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        return [
            {"module": s.module, "feature": s.feature, "description": s.description, "keywords": s.keywords}
            for s in specs
        ]
    if cases:
        return [c.model_dump() for c in cases]
    raise HTTPException(status_code=400, detail="必须提供 text 或 cases")


def _create_group_with_requirements(
    db: Session, user: User, items: List[dict], group_name: Optional[str]
) -> RequirementGroup:
    name = group_name or f"API-{time.strftime('%Y%m%d-%H%M%S')}"
    group = RequirementGroup(name=name, description="通过 Open API 创建", owner_id=user.id)
    db.add(group)
    db.flush()
    for i, it in enumerate(items):
        db.add(
            Requirement(
                group_id=group.id,
                module=it["module"],
                feature=it.get("feature") or it["module"],
                description=it.get("description", ""),
                keywords=it.get("keywords", []),
                sort_order=i,
            )
        )
    db.commit()
    db.refresh(group)
    return group


def _new_job(db: Session, group: RequirementGroup, user: User, total: int,
             llm_config_id: Optional[int], prompt_id: Optional[int]) -> GenerationJob:
    job = GenerationJob(
        group_id=group.id,
        user_id=user.id,
        llm_config_id=llm_config_id,
        prompt_id=prompt_id,
        status="pending",
        total=total,
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    return job


def _cases_out(db: Session, job_id: int) -> List[OpenCaseOut]:
    rows = db.query(GeneratedCase).filter(GeneratedCase.job_id == job_id).order_by(GeneratedCase.id).all()
    return [
        OpenCaseOut(
            case_id=c.case_id, module=c.module, case_type=c.case_type, name=c.name,
            priority=c.priority, preconditions=c.preconditions, steps=c.steps,
            expected=c.expected, keywords=c.keywords, stage=c.stage,
        )
        for c in rows
    ]


def _run_sync(db: Session, user: User, items: List[dict], group_name: Optional[str],
              llm_config_id: Optional[int], prompt_id: Optional[int]) -> OpenGenerateResult:
    if len(items) > SYNC_MAX_ITEMS:
        raise HTTPException(
            status_code=400,
            detail=f"同步生成最多 {SYNC_MAX_ITEMS} 条需求，当前 {len(items)} 条，请改用 /open/generate-async",
        )
    group = _create_group_with_requirements(db, user, items, group_name)
    job = _new_job(db, group, user, len(items), llm_config_id, prompt_id)
    # Synchronous — no cancellation checks needed.
    run_generation(db, job, check_cancel=False)
    db.refresh(job)
    return OpenGenerateResult(
        job_id=job.id, group_id=group.id, status=job.status, total=job.total,
        finished=job.finished, error=job.error, cases=_cases_out(db, job.id),
    )


@router.post("/generate", response_model=OpenGenerateResult, tags=["open-api"])
def open_generate(
    payload: OpenGenerateRequest,
    user: Annotated[User, Depends(get_api_key_user)],
    db: Annotated[Session, Depends(get_db)],
) -> OpenGenerateResult:
    """同步生成：传入 YAML 文本或结构化 cases，阻塞返回完整用例。适合少量需求。"""
    items = _specs_from_request(payload.text, payload.cases)
    return _run_sync(db, user, items, payload.group_name, payload.llm_config_id, payload.prompt_id)


@router.post("/generate-file", response_model=OpenGenerateResult, tags=["open-api"])
async def open_generate_file(
    user: Annotated[User, Depends(get_api_key_user)],
    db: Annotated[Session, Depends(get_db)],
    file: Annotated[UploadFile, File()],
    group_name: Annotated[Optional[str], Form()] = None,
    llm_config_id: Annotated[Optional[int], Form()] = None,
    prompt_id: Annotated[Optional[int], Form()] = None,
) -> OpenGenerateResult:
    """同步生成：上传 YAML 文件，阻塞返回完整用例。适合少量需求。"""
    max_bytes = get_settings().max_upload_size_mb * 1024 * 1024
    raw = await file.read()
    if len(raw) > max_bytes:
        raise HTTPException(status_code=400, detail=f"文件过大，最大 {get_settings().max_upload_size_mb}MB")
    items = _specs_from_request(raw.decode("utf-8", errors="replace"), None)
    return _run_sync(db, user, items, group_name, llm_config_id, prompt_id)


@router.post("/generate-async", response_model=OpenJobStatus, status_code=status.HTTP_202_ACCEPTED, tags=["open-api"])
def open_generate_async(
    payload: OpenGenerateRequest,
    user: Annotated[User, Depends(get_api_key_user)],
    db: Annotated[Session, Depends(get_db)],
) -> OpenJobStatus:
    """异步生成：立即返回 job_id，通过 GET /open/jobs/{id} 轮询结果。适合大批量。"""
    items = _specs_from_request(payload.text, payload.cases)
    group = _create_group_with_requirements(db, user, items, payload.group_name)
    job = _new_job(db, group, user, len(items), payload.llm_config_id, payload.prompt_id)
    generate_job.delay(job.id)
    return OpenJobStatus(
        job_id=job.id, group_id=group.id, status=job.status, total=job.total,
        finished=job.finished, percent=0.0, error=None, cases=[],
    )


@router.get("/jobs/{job_id}", response_model=OpenJobStatus, tags=["open-api"])
def open_job_status(
    job_id: int,
    user: Annotated[User, Depends(get_api_key_user)],
    db: Annotated[Session, Depends(get_db)],
) -> OpenJobStatus:
    """查询异步任务状态与进度；success 时含完整用例。"""
    job = db.get(GenerationJob, job_id)
    if job is None or job.user_id != user.id:
        raise HTTPException(status_code=404, detail="任务不存在")
    total = job.total or 0
    pct = round((job.finished / total * 100) if total else 0, 1)
    cases = _cases_out(db, job.id) if job.status == "success" else []
    return OpenJobStatus(
        job_id=job.id, group_id=job.group_id, status=job.status, total=total,
        finished=job.finished, percent=pct, error=job.error, cases=cases,
    )
