"""Celery application factory.

Imported by the worker entrypoint. Tasks are registered via @shared_task
decorators on individual task functions.
"""
from __future__ import annotations

from celery import Celery

from .config import get_settings

settings = get_settings()

celery_app = Celery(
    "autocase",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=["app.tasks.generation"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=600,         # 10 min hard limit
    task_soft_time_limit=540,    # 9 min soft limit (raises SoftTimeLimitExceeded)
    worker_max_tasks_per_child=200,  # recycle worker to avoid memory leaks
    worker_prefetch_multiplier=1,
)

# Make this the default app so @shared_task instances (e.g. generate_job)
# bind to our Redis broker in BOTH the web and worker processes. Without
# this, the web process would publish to Celery's default amqp://localhost.
celery_app.set_default()
