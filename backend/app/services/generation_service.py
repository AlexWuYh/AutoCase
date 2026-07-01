"""Shared test-case generation logic.

Used by BOTH the Celery async task (tasks/generation.py) and the synchronous
Open API endpoints (api/v1/open_api.py), so the generation behaviour is defined
in exactly one place. Reuses the autocase CLI core (llm_client / generator /
parser) — no duplication of LLM calling or case assembly.
"""
from __future__ import annotations

import logging
from datetime import datetime

from sqlalchemy.orm import Session

from ..models.case import GeneratedCase
from ..models.job import GenerationJob
from ..models.llm_config import LLMConfig
from ..models.prompt import SystemPrompt
from ..models.requirement import Requirement

logger = logging.getLogger("autocase.generation")


def _llm_config_to_dict(cfg: LLMConfig) -> dict:
    """Map an LLMConfig row to the dict shape autocase.llm_client expects."""
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
        "extra_body": cfg.extra_body,
    }


def _mark_failed(db: Session, job: GenerationJob, msg: str) -> None:
    job.status = "failed"
    job.error = msg
    job.finished_at = datetime.utcnow()
    db.commit()


def run_generation(db: Session, job: GenerationJob, *, check_cancel: bool = True) -> GenerationJob:
    """Execute generation for a job in-place, committing progress as it goes.

    - Resolves LLM config + prompt (job-level, falling back to the default).
    - Iterates the group's requirements, calls the autocase LLM client, and
      persists GeneratedCase rows.
    - A single failing requirement does not abort the whole job.
    - When check_cancel is True, honours a status flip to "canceled" between
      requirements (used by the Celery path; the sync API path passes False).

    Returns the same job object (already refreshed with final status).
    """
    # Reuse the existing CLI core modules — no duplication.
    from autocase.llm_client import generate_llm_cases, generate_module_code
    from autocase.generator import llm_items_to_cases
    from autocase.parser import CaseSpec

    if job.status == "canceled":
        return job

    job.status = "running"
    job.started_at = datetime.utcnow()
    job.error = None
    db.commit()

    # Resolve LLM config: prefer job-level, else default.
    if job.llm_config_id:
        llm_row = db.get(LLMConfig, job.llm_config_id)
    else:
        llm_row = db.query(LLMConfig).filter(LLMConfig.is_default.is_(True)).first()
    if llm_row is None:
        _mark_failed(db, job, "没有可用的 LLM 配置（请先在系统配置中创建至少一个 LLM 配置）")
        return job
    llm_config = _llm_config_to_dict(llm_row)

    # Resolve system prompt.
    if job.prompt_id:
        prompt_row = db.get(SystemPrompt, job.prompt_id)
    else:
        prompt_row = db.query(SystemPrompt).filter(SystemPrompt.is_default.is_(True)).first()
    system_prompt = prompt_row.content if prompt_row else "你是测试用例生成器。"

    reqs = (
        db.query(Requirement)
        .filter(Requirement.group_id == job.group_id)
        .order_by(Requirement.sort_order)
        .all()
    )
    if not reqs:
        _mark_failed(db, job, "需求集中没有功能点")
        return job

    job.total = len(reqs)
    job.finished = 0
    db.commit()

    module_cache: dict[str, str] = {}
    next_index = 1

    for idx, req in enumerate(reqs):
        if check_cancel:
            db.refresh(job)
            if job.status == "canceled":
                return job

        try:
            spec = CaseSpec(
                module=req.module,
                feature=req.feature,
                description=req.description,
                keywords=req.keywords,
            )
            if spec.module not in module_cache:
                try:
                    module_cache[spec.module] = generate_module_code(spec.module, llm_config)
                except Exception:
                    module_cache[spec.module] = "MOD"
            spec.module_code = module_cache[spec.module]

            llm_items = generate_llm_cases(spec, llm_config, system_prompt)
            cases, next_index = llm_items_to_cases(llm_items, spec, next_index)

            new_rows = [
                GeneratedCase(
                    job_id=job.id,
                    case_id=c.case_id,
                    module=c.module,
                    case_type=c.case_type,
                    name=c.name,
                    priority=c.priority,
                    preconditions=c.preconditions,
                    steps=c.steps,
                    expected=c.expected,
                    keywords=c.keywords,
                    stage=c.stage,
                )
                for c in cases
            ]
            db.bulk_save_objects(new_rows)
            db.flush()
            job.finished = idx + 1
        except Exception as exc:  # noqa: BLE001 — a bad spec must not kill the job
            logger.exception("Requirement %d failed in job %d", req.id, job.id)
            job.error = f"#{req.id} '{req.feature}' 生成失败: {exc}"
        finally:
            db.commit()

    job.status = "success"
    job.finished_at = datetime.utcnow()
    db.commit()
    return job
