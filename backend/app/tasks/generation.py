"""Celery task: generate test cases for a job."""
from __future__ import annotations

import logging
from datetime import datetime

from celery import shared_task

from ..config import get_settings
from ..database import session_scope
from ..models.case import GeneratedCase
from ..models.job import GenerationJob
from ..models.llm_config import LLMConfig
from ..models.prompt import SystemPrompt
from ..models.requirement import Requirement

logger = logging.getLogger("autocase.tasks")

settings = get_settings()


@shared_task(
    name="app.tasks.generate_job",
    bind=True,
    max_retries=0,
    time_limit=settings.celery_task_time_limit,
    soft_time_limit=settings.celery_task_soft_time_limit,
)
def generate_job(self, job_id: int) -> dict:
    """Generate test cases for every requirement in a group.

    Workflow:
    1. Load the job and mark it running.
    2. Load all requirements in the group, count them.
    3. For each requirement, call the autocase LLM client, convert results,
       and bulk-save generated cases.
    4. On failure: mark job failed, store error message.
    """
    # Reuse the existing CLI core modules — no duplication
    from autocase.llm_client import generate_llm_cases, generate_module_code
    from autocase.generator import llm_items_to_cases
    from autocase.parser import CaseSpec

    with session_scope() as db:
        job = db.get(GenerationJob, job_id)
        if job is None:
            return {"status": "not_found"}
        if job.status in ("canceled",):
            return {"status": "canceled"}

        job.status = "running"
        job.started_at = datetime.utcnow()
        job.error = None
        db.commit()

        # Resolve LLM config — prefer job-level, fall back to default
        if job.llm_config_id:
            llm_row = db.get(LLMConfig, job.llm_config_id)
        else:
            llm_row = db.query(LLMConfig).filter(LLMConfig.is_default.is_(True)).first()
        if llm_row is None:
            err = "没有可用的 LLM 配置（请先在系统配置中创建至少一个 LLM 配置）"
            _mark_failed(db, job, err)
            return {"status": "failed", "error": err}

        llm_config = {
            "provider": llm_row.provider,
            "enabled": llm_row.enabled,
            "api_key_env": llm_row.api_key_env or "",
            "allow_empty_key": llm_row.allow_empty_key,
            "base_url": llm_row.base_url or "",
            "api_mode": llm_row.api_mode,
            "model": llm_row.model,
            "temperature": llm_row.temperature,
            "max_tokens": llm_row.max_tokens,
            "top_p": llm_row.top_p,
            "frequency_penalty": llm_row.frequency_penalty,
            "presence_penalty": llm_row.presence_penalty,
            "retry_count": llm_row.retry_count,
            "debug_log": llm_row.debug_log,
        }

        # Resolve system prompt
        if job.prompt_id:
            prompt_row = db.get(SystemPrompt, job.prompt_id)
        else:
            prompt_row = db.query(SystemPrompt).filter(SystemPrompt.is_default.is_(True)).first()
        system_prompt = prompt_row.content if prompt_row else "你是测试用例生成器。"

        # Load requirements
        reqs = db.query(Requirement).filter(Requirement.group_id == job.group_id).order_by(Requirement.sort_order).all()
        if not reqs:
            err = "需求集中没有功能点"
            _mark_failed(db, job, err)
            return {"status": "failed", "error": err}

        job.total = len(reqs)
        job.finished = 0
        db.commit()

        # Module code cache (per-run, not persisted to DB cache file in Celery)
        module_cache: dict[str, str] = {}
        next_index = 1

        for idx, req in enumerate(reqs):
            # Check cancel flag before each requirement
            db.refresh(job)
            if job.status == "canceled":
                return {"status": "canceled", "finished": job.finished, "total": job.total}

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
            except Exception as exc:
                logger.exception("Requirement %d failed in job %d", req.id, job_id)
                # Single spec failure doesn't abort the whole job — continue
                job.error = f"#{req.id} '{req.feature}' 生成失败: {exc}"
            finally:
                db.commit()

        # All done
        job.status = "success"
        job.finished_at = datetime.utcnow()
        db.commit()

    return {"status": job.status, "total": job.total, "finished": job.finished}


def _mark_failed(db, job: GenerationJob, msg: str) -> None:
    job.status = "failed"
    job.error = msg
    job.finished_at = datetime.utcnow()
    db.commit()
