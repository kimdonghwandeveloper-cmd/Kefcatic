from celery import Celery

from app.core.config import settings

celery_app = Celery(
    "kefcatic",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["app.tasks.assistant_tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    # DB-scan beat: fire every 60 seconds, scan triggers table in the task itself
    beat_schedule={
        "celerybeat-dispatch": {
            "task": "app.tasks.assistant_tasks.celerybeat_dispatch",
            "schedule": 60.0,
        }
    },
)
