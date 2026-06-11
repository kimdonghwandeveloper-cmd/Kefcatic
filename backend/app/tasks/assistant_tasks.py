"""
Celery tasks for assistant execution.

SR-05: All tasks must use get_async_session() context manager.
       Never create DB sessions directly.
"""
import asyncio
import uuid
from datetime import UTC, datetime

from app.tasks.celery_app import celery_app


def _run_async(coro):
    """Run an async coroutine from a sync Celery task."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


@celery_app.task(name="app.tasks.assistant_tasks.celerybeat_dispatch")
def celerybeat_dispatch() -> None:
    """DB-scan beat dispatcher.

    Queries triggers where is_active=True and next_run_at <= now,
    fires run_assistant_task for each, then updates next_run_at.
    Implemented in Phase 1 once the full model layer is wired up.
    """
    _run_async(_celerybeat_dispatch_async())


async def _celerybeat_dispatch_async() -> None:
    from sqlalchemy import select

    from app.core.database import get_async_session
    from app.models.trigger import Trigger

    now = datetime.now(UTC)
    async with get_async_session() as session:  # type: ignore[attr-defined]
        result = await session.execute(
            select(Trigger).where(
                Trigger.is_active.is_(True),
                Trigger.next_run_at <= now,
            )
        )
        triggers = result.scalars().all()
        for trigger in triggers:
            run_assistant_task.delay(
                str(trigger.assistant_id), str(trigger.id)
            )
            # next_run_at will be recalculated in Phase 1 using croniter
            trigger.next_run_at = None
        await session.commit()


@celery_app.task(
    name="app.tasks.assistant_tasks.run_assistant_task",
    bind=True,
    max_retries=3,
    default_retry_delay=60,
)
def run_assistant_task(self, assistant_id: str, trigger_id: str | None = None) -> None:
    """Entry point for assistant execution. Full implementation in Phase 1."""
    _run_async(_run_assistant_task_async(assistant_id, trigger_id))


async def _run_assistant_task_async(
    assistant_id: str, trigger_id: str | None
) -> None:
    # Phase 1: implement full pipeline here
    pass
