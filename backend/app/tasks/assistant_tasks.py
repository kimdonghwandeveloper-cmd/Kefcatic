"""
Celery tasks for assistant execution pipeline.

SR-05: All async DB work uses get_async_session() context manager.
       Never create DB sessions directly; always wrap in try/finally.
"""
import asyncio
import uuid
from datetime import UTC, datetime

from croniter import croniter

from app.tasks.celery_app import celery_app


def _run(coro):
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


# ── Beat dispatcher ───────────────────────────────────────────────────────────

@celery_app.task(name="app.tasks.assistant_tasks.celerybeat_dispatch")
def celerybeat_dispatch() -> None:
    """DB-scan beat: queries triggers table every 60 s and fires due tasks."""
    _run(_celerybeat_dispatch_async())


async def _celerybeat_dispatch_async() -> None:
    from sqlalchemy import select

    from app.core.database import get_async_session
    from app.models.trigger import Trigger

    now = datetime.now(UTC)
    async with get_async_session() as session:
        try:
            result = await session.execute(
                select(Trigger).where(
                    Trigger.is_active.is_(True),
                    Trigger.next_run_at <= now,
                )
            )
            triggers = result.scalars().all()
            for trigger in triggers:
                run_assistant_task.delay(str(trigger.assistant_id), str(trigger.id))
                # Advance next_run_at using croniter
                if trigger.cron_expression:
                    cron = croniter(trigger.cron_expression, now)
                    trigger.next_run_at = cron.get_next(datetime)
                else:
                    trigger.next_run_at = None
        except Exception:
            await session.rollback()
            raise


# ── Assistant execution entry point ──────────────────────────────────────────

@celery_app.task(
    name="app.tasks.assistant_tasks.run_assistant_task",
    bind=True,
    max_retries=3,
    default_retry_delay=60,
)
def run_assistant_task(
    self, assistant_id: str, trigger_id: str | None = None
) -> None:
    try:
        _run(_run_assistant_task_async(uuid.UUID(assistant_id), trigger_id))
    except Exception as exc:
        raise self.retry(exc=exc)


async def _run_assistant_task_async(
    assistant_id: uuid.UUID, trigger_id: str | None
) -> None:
    from sqlalchemy import select

    from app.core.database import get_async_session
    from app.models.assistant import Assistant
    from app.models.task import TaskRun

    async with get_async_session() as session:
        try:
            assistant = await session.get(Assistant, assistant_id)
            if not assistant or not assistant.is_active:
                return

            task_run = TaskRun(
                assistant_id=assistant_id,
                trigger_id=uuid.UUID(trigger_id) if trigger_id else None,
                status="running",
                started_at=datetime.now(UTC),
            )
            session.add(task_run)
            await session.flush()

            await _run_pipeline(session, assistant, task_run)

            task_run.status = "completed"
            task_run.completed_at = datetime.now(UTC)
        except Exception as exc:
            if "task_run" in dir():
                task_run.status = "failed"
                task_run.error_message = str(exc)
                task_run.completed_at = datetime.now(UTC)
            await session.rollback()
            raise


async def _run_pipeline(session, assistant, task_run) -> None:
    """Full execution pipeline: fetch → classify → draft → gate."""
    if assistant.role_type == "youtube_moderator":
        await _youtube_pipeline(session, assistant, task_run)
    elif assistant.role_type == "gmail_responder":
        await _gmail_pipeline(session, assistant, task_run)


async def _youtube_pipeline(session, assistant, task_run) -> None:
    from sqlalchemy import select

    from app.models.connector import AssistantConnector
    from app.services.action_engine import execute_action
    from app.services.connector_credential_service import ConnectorCredentialService
    from app.services.llm_service import LLMService
    from app.connectors.youtube import YouTubeConnector

    # Fetch the YouTube credential attached to this assistant
    result = await session.execute(
        select(AssistantConnector).where(
            AssistantConnector.assistant_id == assistant.id,
            AssistantConnector.connector_type == "youtube",
        )
    )
    ac = result.scalar_one_or_none()
    if not ac:
        return

    cred_service = ConnectorCredentialService(session)
    credentials = await cred_service.get_decrypted(ac.credential_id)

    connector = YouTubeConnector(credentials=credentials, config=dict(ac.config or {}))
    items = await connector.list_items(max_results=50)

    llm = LLMService()
    categories = ["spam", "question", "positive", "negative", "other"]

    for item in items:
        classification = await llm.classify_comment(item.content, categories)

        if classification.category == "spam":
            await execute_action(
                session,
                task_run_id=task_run.id,
                action_type="youtube.comment.hide",
                assistant_id=assistant.id,
                input_data={"comment_id": item.id},
            )
        elif classification.category == "question":
            draft = await llm.generate_reply_draft(
                item.content,
                assistant_system_prompt=assistant.system_prompt or "",
            )
            await execute_action(
                session,
                task_run_id=task_run.id,
                action_type="youtube.comment.reply",
                assistant_id=assistant.id,
                input_data={"comment_id": item.id, "text": draft.text},
            )

    task_run.result_summary = {
        "total": len(items),
        "categories": categories,
    }


async def _gmail_pipeline(session, assistant, task_run) -> None:
    """Gmail responder pipeline: fetch unread → classify → draft reply → gate."""
    from sqlalchemy import select

    from app.connectors.gmail import GmailConnector
    from app.models.connector import AssistantConnector
    from app.services.action_engine import execute_action
    from app.services.connector_credential_service import ConnectorCredentialService
    from app.services.llm_service import LLMService

    result = await session.execute(
        select(AssistantConnector).where(
            AssistantConnector.assistant_id == assistant.id,
            AssistantConnector.connector_type == "gmail",
        )
    )
    ac = result.scalar_one_or_none()
    if not ac:
        return

    cred_service = ConnectorCredentialService(session)
    credentials = await cred_service.get_decrypted(ac.credential_id)

    connector = GmailConnector(credentials=credentials, config=dict(ac.config or {}))
    messages = await connector.list_items(max_results=20)

    llm = LLMService()
    categories = ["urgent", "question", "newsletter", "notification", "other"]

    processed = 0
    for msg in messages:
        classification = await llm.classify_comment(msg.content, categories)

        if classification.category in ("urgent", "question"):
            draft = await llm.generate_reply_draft(
                msg.content,
                assistant_system_prompt=assistant.system_prompt or "",
            )
            meta = msg.metadata or {}
            await execute_action(
                session,
                task_run_id=task_run.id,
                action_type="gmail.draft.create",
                assistant_id=assistant.id,
                input_data={
                    "thread_id": meta.get("thread_id", msg.id),
                    "to": meta.get("from", ""),
                    "subject": f"Re: {meta.get('subject', '')}",
                    "body": draft.text,
                },
            )
        elif classification.category in ("newsletter", "notification"):
            # Auto-label as read (low-risk, auto mode)
            await execute_action(
                session,
                task_run_id=task_run.id,
                action_type="gmail.message.label",
                assistant_id=assistant.id,
                input_data={
                    "message_id": msg.id,
                    "add_labels": [],
                    "remove_labels": ["UNREAD"],
                },
            )

        processed += 1

    task_run.result_summary = {
        "total": len(messages),
        "processed": processed,
    }


# ── Post-approval execution ───────────────────────────────────────────────────

@celery_app.task(
    name="app.tasks.assistant_tasks.execute_approved_action",
    bind=True,
    max_retries=3,
    default_retry_delay=30,
)
def execute_approved_action(self, action_log_id: str) -> None:
    try:
        _run(_execute_approved_action_async(uuid.UUID(action_log_id)))
    except Exception as exc:
        raise self.retry(exc=exc)


async def _execute_approved_action_async(action_log_id: uuid.UUID) -> None:
    from datetime import UTC, datetime

    from app.core.database import get_async_session
    from app.models.action import ActionLog
    from app.models.assistant import Assistant
    from app.models.connector import AssistantConnector
    from app.models.task import TaskRun
    from app.services.action_engine import ACTION_REGISTRY
    from app.services.connector_credential_service import ConnectorCredentialService
    from app.connectors.youtube import YouTubeConnector

    async with get_async_session() as session:
        try:
            action_log = await session.get(ActionLog, action_log_id)
            if not action_log or action_log.status != "approved":
                return

            task_run = await session.get(TaskRun, action_log.task_run_id)
            assistant = await session.get(Assistant, task_run.assistant_id)

            result = await session.execute(
                __import__("sqlalchemy", fromlist=["select"]).select(AssistantConnector).where(
                    AssistantConnector.assistant_id == assistant.id,
                    AssistantConnector.connector_type == "youtube",
                )
            )
            ac = result.scalar_one_or_none()
            if not ac:
                return

            cred_service = ConnectorCredentialService(session)
            credentials = await cred_service.get_decrypted(ac.credential_id)
            connector = YouTubeConnector(credentials=credentials)

            input_data = action_log.modified_input or action_log.input_data or {}

            if action_log.action_type == "youtube.comment.reply":
                item = await connector.create_item(input_data)
                action_log.output_data = {"reply_id": item.id}
                action_log.external_resource_id = item.id
                action_log.rollback_data = {"reply_id": item.id}
            elif action_log.action_type == "youtube.comment.hide":
                success = await connector.delete_item(input_data["comment_id"])
                action_log.output_data = {"success": success}
                action_log.external_resource_id = input_data["comment_id"]

            action_log.status = "executed"
            action_log.executed_at = datetime.now(UTC)
        except Exception:
            if action_log:
                action_log.status = "failed"
            await session.rollback()
            raise


# ── Rollback ──────────────────────────────────────────────────────────────────

@celery_app.task(
    name="app.tasks.assistant_tasks.rollback_action_task",
    bind=True,
    max_retries=2,
    default_retry_delay=30,
)
def rollback_action_task(self, action_log_id: str) -> None:
    try:
        _run(_rollback_action_async(uuid.UUID(action_log_id)))
    except Exception as exc:
        raise self.retry(exc=exc)


async def _rollback_action_async(action_log_id: uuid.UUID) -> None:
    from app.core.database import get_async_session
    from app.models.action import ActionLog
    from app.models.assistant import Assistant
    from app.models.connector import AssistantConnector
    from app.models.task import TaskRun
    from app.services.connector_credential_service import ConnectorCredentialService
    from app.connectors.youtube import YouTubeConnector
    from sqlalchemy import select

    async with get_async_session() as session:
        try:
            action_log = await session.get(ActionLog, action_log_id)
            # SR-02: never rollback without external_resource_id
            if not action_log or not action_log.external_resource_id:
                return

            task_run = await session.get(TaskRun, action_log.task_run_id)
            assistant = await session.get(Assistant, task_run.assistant_id)

            result = await session.execute(
                select(AssistantConnector).where(
                    AssistantConnector.assistant_id == assistant.id,
                    AssistantConnector.connector_type == "youtube",
                )
            )
            ac = result.scalar_one_or_none()
            if not ac:
                return

            cred_service = ConnectorCredentialService(session)
            credentials = await cred_service.get_decrypted(ac.credential_id)
            connector = YouTubeConnector(credentials=credentials)

            if action_log.action_type == "youtube.comment.reply":
                # Delete the reply that was posted
                await connector.delete_item(action_log.external_resource_id)
            elif action_log.action_type == "youtube.comment.hide":
                # Restore comment (set back to published)
                import httpx
                async with httpx.AsyncClient() as client:
                    await client.post(
                        "https://www.googleapis.com/youtube/v3/comments/setModerationStatus",
                        headers={"Authorization": f"Bearer {credentials['access_token']}"},
                        params={
                            "id": action_log.external_resource_id,
                            "moderationStatus": "published",
                        },
                    )

            action_log.status = "rolled_back"
        except Exception:
            await session.rollback()
            raise
