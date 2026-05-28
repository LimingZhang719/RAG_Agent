from __future__ import annotations

from celery import Celery

from app.core.config import settings


def _resolve_broker_url() -> str:
    return settings.celery_broker_url or settings.redis_url


def _resolve_backend_url() -> str:
    return settings.celery_result_backend or settings.redis_url


celery_app = Celery(
    "rag_agent",
    broker=_resolve_broker_url(),
    backend=_resolve_backend_url(),
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    include=["app.workers.document_tasks"],
)
