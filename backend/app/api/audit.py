"""Audit log endpoints — full execution history."""
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_async_session
from app.core.deps import get_current_user
from app.models.action import ActionLog
from app.models.assistant import Assistant
from app.models.task import TaskRun
from app.models.user import User
from app.schemas.audit import PaginatedTaskRuns, TaskRunDetailOut, TaskRunListOut

router = APIRouter(prefix="/audit", tags=["audit"])


@router.get("/task-runs", response_model=PaginatedTaskRuns)
async def list_task_runs(
    current_user: Annotated[User, Depends(get_current_user)],
    session: AsyncSession = Depends(get_async_session),
    assistant_id: uuid.UUID | None = Query(None),
    run_status: str | None = Query(None, alias="status"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> dict:
    base_query = (
        select(TaskRun)
        .join(Assistant, TaskRun.assistant_id == Assistant.id)
        .where(Assistant.user_id == current_user.id)
    )
    if assistant_id:
        base_query = base_query.where(TaskRun.assistant_id == assistant_id)
    if run_status:
        base_query = base_query.where(TaskRun.status == run_status)

    count_result = await session.execute(
        select(func.count()).select_from(base_query.subquery())
    )
    total = count_result.scalar_one()

    result = await session.execute(
        base_query.order_by(TaskRun.started_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    items = result.scalars().all()
    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.get("/task-runs/{task_run_id}", response_model=TaskRunDetailOut)
async def get_task_run_detail(
    task_run_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    session: AsyncSession = Depends(get_async_session),
) -> TaskRun:
    result = await session.execute(
        select(TaskRun)
        .where(TaskRun.id == task_run_id)
        .options(selectinload(TaskRun.action_logs))
    )
    task_run = result.scalar_one_or_none()
    if not task_run:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="TaskRun not found")

    assistant = await session.get(Assistant, task_run.assistant_id)
    if not assistant or assistant.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    return task_run


@router.get("/action-logs", response_model=list)
async def list_action_logs(
    current_user: Annotated[User, Depends(get_current_user)],
    session: AsyncSession = Depends(get_async_session),
    action_type: str | None = Query(None),
    log_status: str | None = Query(None, alias="status"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> list[ActionLog]:
    query = (
        select(ActionLog)
        .join(TaskRun, ActionLog.task_run_id == TaskRun.id)
        .join(Assistant, TaskRun.assistant_id == Assistant.id)
        .where(Assistant.user_id == current_user.id)
    )
    if action_type:
        query = query.where(ActionLog.action_type == action_type)
    if log_status:
        query = query.where(ActionLog.status == log_status)

    result = await session.execute(
        query.order_by(ActionLog.executed_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    return result.scalars().all()
