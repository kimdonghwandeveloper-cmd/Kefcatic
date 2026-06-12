"""Approval inbox endpoints.

SR-01: Only 'approved' action_logs trigger actual execution.
SR-02: Rollback only when external_resource_id is present.
SR-04: No duplicate pending approval_requests.
"""
import uuid
from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_async_session
from app.core.deps import get_current_user
from app.models.action import ActionLog
from app.models.approval import ApprovalRequest
from app.models.assistant import Assistant
from app.models.task import TaskRun
from app.models.user import User
from app.schemas.approval import (
    ApprovalDecision,
    ApprovalRequestOut,
    BulkApproveRequest,
)

router = APIRouter(prefix="/approvals", tags=["approvals"])


async def _verify_approval_ownership(
    approval_req: ApprovalRequest,
    current_user: User,
    session: AsyncSession,
) -> ActionLog:
    """Ensure the approval_request belongs to an assistant owned by the user."""
    action_log = await session.get(ActionLog, approval_req.action_log_id)
    task_run = await session.get(TaskRun, action_log.task_run_id)
    assistant = await session.get(Assistant, task_run.assistant_id)
    if not assistant or assistant.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    return action_log


@router.get("", response_model=list[ApprovalRequestOut])
async def list_approvals(
    current_user: Annotated[User, Depends(get_current_user)],
    session: AsyncSession = Depends(get_async_session),
    approval_status: str = Query("pending", alias="status"),
) -> list[ApprovalRequest]:
    """List approval requests for the current user, filtered by status."""
    # Join through action_logs → task_runs → assistants to filter by user
    result = await session.execute(
        select(ApprovalRequest)
        .join(ActionLog, ApprovalRequest.action_log_id == ActionLog.id)
        .join(TaskRun, ActionLog.task_run_id == TaskRun.id)
        .join(Assistant, TaskRun.assistant_id == Assistant.id)
        .where(
            Assistant.user_id == current_user.id,
            ApprovalRequest.status == approval_status,
        )
        .options(selectinload(ApprovalRequest.action_log))
        .order_by(ApprovalRequest.requested_at.desc())
    )
    return result.scalars().all()


@router.post("/{action_log_id}/approve", response_model=ApprovalRequestOut)
async def approve_action(
    action_log_id: uuid.UUID,
    body: ApprovalDecision,
    current_user: Annotated[User, Depends(get_current_user)],
    session: AsyncSession = Depends(get_async_session),
) -> ApprovalRequest:
    result = await session.execute(
        select(ApprovalRequest).where(
            ApprovalRequest.action_log_id == action_log_id,
            ApprovalRequest.status == "pending",
        )
    )
    approval_req = result.scalar_one_or_none()
    if not approval_req:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pending approval not found")

    action_log = await _verify_approval_ownership(approval_req, current_user, session)

    approval_req.status = "approved"
    approval_req.reviewed_by = current_user.id
    approval_req.reviewed_at = datetime.now(UTC)
    approval_req.reviewer_note = body.reviewer_note
    approval_req.modified_input = body.modified_input

    action_log.status = "approved"
    action_log.approved_by = current_user.id
    action_log.approved_at = datetime.now(UTC)
    if body.modified_input:
        action_log.input_data = body.modified_input

    await session.flush()

    # Fire the actual execution via Celery
    from app.tasks.assistant_tasks import execute_approved_action
    execute_approved_action.delay(str(action_log_id))

    return approval_req


@router.post("/{action_log_id}/reject", response_model=ApprovalRequestOut)
async def reject_action(
    action_log_id: uuid.UUID,
    body: ApprovalDecision,
    current_user: Annotated[User, Depends(get_current_user)],
    session: AsyncSession = Depends(get_async_session),
) -> ApprovalRequest:
    result = await session.execute(
        select(ApprovalRequest).where(
            ApprovalRequest.action_log_id == action_log_id,
            ApprovalRequest.status == "pending",
        )
    )
    approval_req = result.scalar_one_or_none()
    if not approval_req:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pending approval not found")

    action_log = await _verify_approval_ownership(approval_req, current_user, session)

    approval_req.status = "rejected"
    approval_req.reviewed_by = current_user.id
    approval_req.reviewed_at = datetime.now(UTC)
    approval_req.reviewer_note = body.reviewer_note

    action_log.status = "rejected"
    return approval_req


@router.post("/bulk-approve", status_code=status.HTTP_200_OK)
async def bulk_approve(
    body: BulkApproveRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    session: AsyncSession = Depends(get_async_session),
) -> dict:
    approved_ids = []
    for log_id_str in body.action_log_ids:
        log_id = uuid.UUID(log_id_str)
        result = await session.execute(
            select(ApprovalRequest).where(
                ApprovalRequest.action_log_id == log_id,
                ApprovalRequest.status == "pending",
            )
        )
        approval_req = result.scalar_one_or_none()
        if not approval_req:
            continue
        try:
            action_log = await _verify_approval_ownership(approval_req, current_user, session)
        except HTTPException:
            continue

        approval_req.status = "approved"
        approval_req.reviewed_by = current_user.id
        approval_req.reviewed_at = datetime.now(UTC)
        action_log.status = "approved"
        action_log.approved_by = current_user.id
        action_log.approved_at = datetime.now(UTC)
        approved_ids.append(log_id_str)

    await session.flush()

    from app.tasks.assistant_tasks import execute_approved_action
    for log_id_str in approved_ids:
        execute_approved_action.delay(log_id_str)

    return {"approved": len(approved_ids), "ids": approved_ids}


@router.post("/{action_log_id}/rollback", status_code=status.HTTP_200_OK)
async def rollback_action(
    action_log_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    session: AsyncSession = Depends(get_async_session),
) -> dict:
    action_log = await session.get(ActionLog, action_log_id)
    if not action_log:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Action log not found")

    # SR-02: never attempt rollback without external_resource_id
    if not action_log.external_resource_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot rollback: external_resource_id is not set (SR-02)",
        )

    # Ownership check
    task_run = await session.get(TaskRun, action_log.task_run_id)
    assistant = await session.get(Assistant, task_run.assistant_id)
    if not assistant or assistant.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    from app.tasks.assistant_tasks import rollback_action_task
    rollback_action_task.delay(str(action_log_id))

    return {"status": "rollback_queued", "action_log_id": str(action_log_id)}
