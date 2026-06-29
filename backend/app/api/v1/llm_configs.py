"""LLM configuration endpoints."""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from ...database import get_db
from ...deps import require_admin
from ...models.llm_config import LLMConfig
from ...models.user import User
from ...schemas.llm_config import (
    LLMConfigCreate,
    LLMConfigOut,
    LLMConfigTestPayload,
    LLMConfigTestResult,
    LLMConfigUpdate,
)
from ...schemas.common import PageResponse
from ...services.llm_service import test_llm_connection
from ...config import get_settings

router = APIRouter()


def _to_config_dict(cfg: LLMConfig) -> dict:
    return {
        "provider": cfg.provider,
        "enabled": cfg.enabled,
        "api_key_env": cfg.api_key_env or "",
        "allow_empty_key": cfg.allow_empty_key,
        "base_url": cfg.base_url or "",
        "api_mode": cfg.api_mode,
        "model": cfg.model,
        "temperature": cfg.temperature,
        "max_tokens": cfg.max_tokens,
        "top_p": cfg.top_p,
        "frequency_penalty": cfg.frequency_penalty,
        "presence_penalty": cfg.presence_penalty,
        "retry_count": cfg.retry_count,
        "debug_log": cfg.debug_log,
    }


def _ensure_single_default(db: Session, cfg: LLMConfig) -> None:
    """If this config is the default, clear is_default on all others."""
    if cfg.is_default:
        db.query(LLMConfig).filter(
            LLMConfig.id != cfg.id, LLMConfig.is_default.is_(True)
        ).update({"is_default": False}, synchronize_session=False)


@router.get("", response_model=PageResponse[LLMConfigOut], tags=["llm-configs"])
def list_configs(
    _: Annotated[User, Depends(require_admin)],
    db: Annotated[Session, Depends(get_db)],
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> PageResponse[LLMConfigOut]:
    stmt = select(LLMConfig).order_by(LLMConfig.is_default.desc(), LLMConfig.id.desc())
    total = len(db.execute(stmt).all())
    rows = db.execute(stmt.offset((page - 1) * page_size).limit(page_size)).scalars().all()
    return PageResponse(
        items=[LLMConfigOut.model_validate(r) for r in rows],
        total=total, page=page, page_size=page_size,
    )


@router.post("", response_model=LLMConfigOut, status_code=status.HTTP_201_CREATED, tags=["llm-configs"])
def create_config(
    payload: LLMConfigCreate,
    _: Annotated[User, Depends(require_admin)],
    db: Annotated[Session, Depends(get_db)],
) -> LLMConfigOut:
    cfg = LLMConfig(**payload.model_dump())
    db.add(cfg)
    db.flush()
    _ensure_single_default(db, cfg)
    db.commit()
    db.refresh(cfg)
    return LLMConfigOut.model_validate(cfg)


@router.get("/{config_id}", response_model=LLMConfigOut, tags=["llm-configs"])
def get_config(
    config_id: int,
    _: Annotated[User, Depends(require_admin)],
    db: Annotated[Session, Depends(get_db)],
) -> LLMConfigOut:
    cfg = db.get(LLMConfig, config_id)
    if cfg is None:
        raise HTTPException(status_code=404, detail="LLM 配置不存在")
    return LLMConfigOut.model_validate(cfg)


@router.put("/{config_id}", response_model=LLMConfigOut, tags=["llm-configs"])
def update_config(
    config_id: int,
    payload: LLMConfigUpdate,
    _: Annotated[User, Depends(require_admin)],
    db: Annotated[Session, Depends(get_db)],
) -> LLMConfigOut:
    cfg = db.get(LLMConfig, config_id)
    if cfg is None:
        raise HTTPException(status_code=404, detail="LLM 配置不存在")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(cfg, key, value)
    _ensure_single_default(db, cfg)
    db.commit()
    db.refresh(cfg)
    return LLMConfigOut.model_validate(cfg)


@router.delete("/{config_id}", tags=["llm-configs"])
def delete_config(
    config_id: int,
    _: Annotated[User, Depends(require_admin)],
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    cfg = db.get(LLMConfig, config_id)
    if cfg is None:
        raise HTTPException(status_code=404, detail="LLM 配置不存在")
    if cfg.is_default:
        raise HTTPException(status_code=400, detail="不能删除默认配置，请先将其他配置设为默认")
    db.delete(cfg)
    db.commit()
    return {"message": "已删除"}


@router.post("/{config_id}/test", response_model=LLMConfigTestResult, tags=["llm-configs"])
def test_config(
    config_id: int,
    _: Annotated[User, Depends(require_admin)],
    db: Annotated[Session, Depends(get_db)],
    payload: LLMConfigTestPayload | None = None,
) -> LLMConfigTestResult:
    cfg = db.get(LLMConfig, config_id)
    if cfg is None:
        raise HTTPException(status_code=404, detail="LLM 配置不存在")
    import time
    t0 = time.perf_counter()
    try:
        reply = test_llm_connection(_to_config_dict(cfg), test_message=payload.message if payload else "Say OK")
        elapsed = (time.perf_counter() - t0) * 1000
        return LLMConfigTestResult(success=True, elapsed_ms=elapsed, message=reply)
    except Exception as e:
        elapsed = (time.perf_counter() - t0) * 1000
        return LLMConfigTestResult(success=False, elapsed_ms=elapsed, message=str(e))
