"""Celery task: generate test cases for a job.

Thin wrapper around services.generation_service.run_generation so the Celery
path and the synchronous Open API path share one implementation.
"""
from __future__ import annotations

import logging

from celery import shared_task

from ..config import get_settings
from ..database import session_scope
from ..models.job import GenerationJob
from ..services.generation_service import run_generation

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
    """Load the job and run generation. Honours cancellation between specs."""
    with session_scope() as db:
        job = db.get(GenerationJob, job_id)
        if job is None:
            return {"status": "not_found"}
        if job.status == "canceled":
            return {"status": "canceled"}
        run_generation(db, job, check_cancel=True)
        return {"status": job.status, "total": job.total, "finished": job.finished}
