"""Celery task stubs. Real generation task lands in Phase 5."""
from celery import shared_task


@shared_task(name="app.tasks.ping")
def ping() -> str:
    """Health-check task used to verify the worker is reachable."""
    return "pong"
