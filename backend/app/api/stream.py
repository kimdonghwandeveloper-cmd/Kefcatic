"""Server-Sent Events endpoint for live task_run status updates."""
import asyncio
import json
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_session
from app.core.deps import get_current_user
from app.models.assistant import Assistant
from app.models.task import TaskRun
from app.models.user import User

router = APIRouter(prefix="/stream", tags=["stream"])

_TERMINAL_STATUSES = {"completed", "failed", "cancelled"}


@router.get("/task-runs/{task_run_id}")
async def stream_task_run(
    task_run_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    session: AsyncSession = Depends(get_async_session),
) -> StreamingResponse:
    # Validate ownership before streaming
    task_run = await session.get(TaskRun, task_run_id)
    if not task_run:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="TaskRun not found")
    assistant = await session.get(Assistant, task_run.assistant_id)
    if not assistant or assistant.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    async def event_generator():
        last_status = None
        poll_interval = 1.5  # seconds

        for _ in range(120):  # max 3 minutes
            # Re-fetch in a fresh session per poll cycle
            async with get_async_session() as poll_session:
                tr = await poll_session.get(TaskRun, task_run_id)
                if not tr:
                    break
                current_status = tr.status
                if current_status != last_status:
                    payload = json.dumps(
                        {
                            "task_run_id": str(task_run_id),
                            "status": current_status,
                            "error_message": tr.error_message,
                            "result_summary": tr.result_summary,
                        }
                    )
                    yield f"data: {payload}\n\n"
                    last_status = current_status

                if current_status in _TERMINAL_STATUSES:
                    yield "data: {\"event\": \"done\"}\n\n"
                    return

            await asyncio.sleep(poll_interval)

        yield "data: {\"event\": \"timeout\"}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/assistants/{assistant_id}/state")
async def get_assistant_state(
    assistant_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    session: AsyncSession = Depends(get_async_session),
) -> dict:
    """Return the current cat state for an assistant (used by Cat Room)."""
    from sqlalchemy import select

    assistant = await session.get(Assistant, assistant_id)
    if not assistant or assistant.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assistant not found")

    # Get the most recent non-terminal task_run
    result = await session.execute(
        select(TaskRun)
        .where(TaskRun.assistant_id == assistant_id)
        .order_by(TaskRun.started_at.desc())
        .limit(1)
    )
    latest_run = result.scalar_one_or_none()

    cat_state = _derive_cat_state(latest_run)
    return {
        "assistant_id": str(assistant_id),
        "cat_state": cat_state,
        "status_text": _state_text(assistant.role_type, cat_state),
        "task_run_id": str(latest_run.id) if latest_run else None,
        "task_run_status": latest_run.status if latest_run else None,
    }


def _derive_cat_state(task_run: TaskRun | None) -> str:
    if task_run is None:
        return "idle"
    mapping = {
        "pending": "watching",
        "running": "reading",
        "waiting_approval": "waiting_approval",
        "completed": "done",
        "failed": "error",
        "cancelled": "idle",
    }
    return mapping.get(task_run.status, "idle")


def _state_text(role_type: str | None, cat_state: str) -> str:
    texts: dict[str, dict[str, str]] = {
        "youtube_moderator": {
            "idle": "쉬고 있어요.",
            "watching": "새 댓글이 있는지 살펴보고 있어요.",
            "reading": "댓글을 하나씩 읽고 있어요.",
            "sorting": "댓글을 분류하고 있어요.",
            "drafting": "답글 초안을 작성하고 있어요.",
            "waiting_approval": "처리할 댓글을 물어와서 기다리고 있어요.",
            "executing": "댓글을 처리하고 있어요.",
            "done": "오늘 할 일을 다 마쳤어요.",
            "error": "도움이 필요해요.",
        },
        "gmail_responder": {
            "idle": "쉬고 있어요.",
            "watching": "받은편지함을 확인하고 있어요.",
            "reading": "메일을 읽고 있어요.",
            "drafting": "답장 초안을 작성하고 있어요.",
            "waiting_approval": "답장 초안을 물어와서 기다리고 있어요.",
            "executing": "메일을 처리하고 있어요.",
            "done": "오늘 메일을 모두 처리했어요.",
            "error": "도움이 필요해요.",
        },
    }
    role_texts = texts.get(role_type or "", texts["youtube_moderator"])
    return role_texts.get(cat_state, "작업 중이에요.")
