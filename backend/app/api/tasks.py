"""Task run endpoints — manual trigger and status polling."""
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_session
from app.core.deps import get_current_user
from app.models.assistant import Assistant
from app.models.task import TaskRun
from app.models.user import User
from app.schemas.task import TaskRunOut

router = APIRouter(prefix="/task-runs", tags=["task-runs"])


@router.post("/{assistant_id}/trigger", response_model=TaskRunOut, status_code=status.HTTP_202_ACCEPTED)
async def trigger_assistant(
    assistant_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    session: AsyncSession = Depends(get_async_session),
) -> TaskRun:
    assistant = await session.get(Assistant, assistant_id)
    if not assistant or assistant.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assistant not found")
    if not assistant.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Assistant is not active")

    from app.tasks.assistant_tasks import run_assistant_task

    # Persist a pending task_run so the client can poll its status
    task_run = TaskRun(
        assistant_id=assistant_id,
        trigger_id=None,
        status="pending",
    )
    session.add(task_run)
    await session.flush()

    run_assistant_task.delay(str(assistant_id))
    return task_run


@router.get("/{task_run_id}", response_model=TaskRunOut)
async def get_task_run(
    task_run_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    session: AsyncSession = Depends(get_async_session),
) -> TaskRun:
    task_run = await session.get(TaskRun, task_run_id)
    if not task_run:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="TaskRun not found")

    # Verify ownership via assistant
    assistant = await session.get(Assistant, task_run.assistant_id)
    if not assistant or assistant.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    return task_run
