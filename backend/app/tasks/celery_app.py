from celery import Celery
from celery.schedules import crontab

from app.core.config import settings

celery_app = Celery(
    "kefcatic",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["app.tasks.assistant_tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    beat_schedule={
        # DB-scan dispatcher: runs every minute, queries triggers table (SR-05 compliant)
        "celerybeat-dispatch": {
            "task": "app.tasks.assistant_tasks.celerybeat_dispatch",
            "schedule": crontab(minute="*"),
        },
    },
)
