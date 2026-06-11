import asyncio
import uuid
from datetime import datetime, timezone

from sqlalchemy import select

from app.tasks.celery_app import celery_app


def _run_async(coro):  # type: ignore[no-untyped-def]
    """Run an async coroutine from a sync Celery task."""
    return asyncio.get_event_loop().run_until_complete(coro)


@celery_app.task(name="app.tasks.assistant_tasks.celerybeat_dispatch", bind=True)
def celerybeat_dispatch(self) -> None:  # type: ignore[no-untyped-def]
    """
    DB-scan Beat dispatcher — runs every minute.
    Queries triggers table for active rows where next_run_at has passed,
    fires run_assistant_task per match, and updates next_run_at.
    Never injects schedules directly into Redis.
    """
    _run_async(_dispatch())


async def _dispatch() -> None:
    from app.core.database import get_async_session
    from app.models import Trigger

    now = datetime.now(timezone.utc)

    async with get_async_session() as session:
        result = await session.execute(
            select(Trigger).where(
                Trigger.is_active == True,  # noqa: E712
                Trigger.next_run_at <= now,
            )
        )
        triggers = result.scalars().all()

        for trigger in triggers:
            run_assistant_task.delay(str(trigger.assistant_id), str(trigger.id))
            # next_run_at will be recalculated in run_assistant_task after cron parsing
            trigger.next_run_at = None  # cleared until task recalculates
        await session.flush()


@celery_app.task(
    name="app.tasks.assistant_tasks.run_assistant_task",
    bind=True,
    max_retries=3,
    default_retry_delay=60,
)
def run_assistant_task(self, assistant_id: str, trigger_id: str | None = None) -> None:  # type: ignore[no-untyped-def]
    """Entry point for assistant execution. Creates a TaskRun and begins processing."""
    _run_async(_run_assistant(uuid.UUID(assistant_id), uuid.UUID(trigger_id) if trigger_id else None))


async def _run_assistant(assistant_id: uuid.UUID, trigger_id: uuid.UUID | None) -> None:
    from datetime import timezone

    from app.core.database import get_async_session
    from app.models import TaskRun

    async with get_async_session() as session:
        task_run = TaskRun(
            assistant_id=assistant_id,
            trigger_id=trigger_id,
            status="running",
            started_at=datetime.now(timezone.utc),
        )
        session.add(task_run)
        await session.flush()
        # Phase 1+ will add actual execution logic here


@celery_app.task(name="app.tasks.assistant_tasks.execute_action", bind=True)
def execute_action(self, action_log_id: str) -> None:  # type: ignore[no-untyped-def]
    """Execute an approved action. Phase 1 stub."""
