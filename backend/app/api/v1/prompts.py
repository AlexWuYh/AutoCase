"""System prompt templates endpoints."""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from ...database import get_db
from ...deps import require_admin
from ...models.prompt import SystemPrompt
from ...models.user import User
from ...schemas.common import PageResponse
from ...schemas.llm_config import (
    SystemPromptCreate,
    SystemPromptOut,
    SystemPromptUpdate,
)

router = APIRouter()


def _ensure_single_default(db: Session, p: SystemPrompt) -> None:
    if p.is_default:
        db.query(SystemPrompt).filter(
            SystemPrompt.id != p.id, SystemPrompt.is_default.is_(True)
        ).update({"is_default": False}, synchronize_session=False)


@router.get("", response_model=PageResponse[SystemPromptOut], tags=["system-prompts"])
def list_prompts(
    _: Annotated[User, Depends(require_admin)],
    db: Annotated[Session, Depends(get_db)],
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> PageResponse[SystemPromptOut]:
    stmt = select(SystemPrompt).order_by(SystemPrompt.is_default.desc(), SystemPrompt.id.desc())
    total = len(db.execute(stmt).all())
    rows = db.execute(stmt.offset((page - 1) * page_size).limit(page_size)).scalars().all()
    return PageResponse(
        items=[SystemPromptOut.model_validate(r) for r in rows],
        total=total, page=page, page_size=page_size,
    )


@router.post("", response_model=SystemPromptOut, status_code=status.HTTP_201_CREATED, tags=["system-prompts"])
def create_prompt(
    payload: SystemPromptCreate,
    _: Annotated[User, Depends(require_admin)],
    db: Annotated[Session, Depends(get_db)],
) -> SystemPromptOut:
    p = SystemPrompt(**payload.model_dump())
    db.add(p)
    db.flush()
    _ensure_single_default(db, p)
    db.commit()
    db.refresh(p)
    return SystemPromptOut.model_validate(p)


@router.get("/{prompt_id}", response_model=SystemPromptOut, tags=["system-prompts"])
def get_prompt(
    prompt_id: int,
    _: Annotated[User, Depends(require_admin)],
    db: Annotated[Session, Depends(get_db)],
) -> SystemPromptOut:
    p = db.get(SystemPrompt, prompt_id)
    if p is None:
        raise HTTPException(status_code=404, detail="Prompt 不存在")
    return SystemPromptOut.model_validate(p)


@router.put("/{prompt_id}", response_model=SystemPromptOut, tags=["system-prompts"])
def update_prompt(
    prompt_id: int,
    payload: SystemPromptUpdate,
    _: Annotated[User, Depends(require_admin)],
    db: Annotated[Session, Depends(get_db)],
) -> SystemPromptOut:
    p = db.get(SystemPrompt, prompt_id)
    if p is None:
        raise HTTPException(status_code=404, detail="Prompt 不存在")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(p, key, value)
    _ensure_single_default(db, p)
    db.commit()
    db.refresh(p)
    return SystemPromptOut.model_validate(p)


@router.delete("/{prompt_id}", tags=["system-prompts"])
def delete_prompt(
    prompt_id: int,
    _: Annotated[User, Depends(require_admin)],
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    p = db.get(SystemPrompt, prompt_id)
    if p is None:
        raise HTTPException(status_code=404, detail="Prompt 不存在")
    if p.is_default:
        raise HTTPException(status_code=400, detail="不能删除默认 Prompt，请先将其他 Prompt 设为默认")
    db.delete(p)
    db.commit()
    return {"message": "已删除"}
