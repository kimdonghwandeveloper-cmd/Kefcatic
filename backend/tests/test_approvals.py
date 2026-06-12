"""Integration tests for the approval system."""
import uuid
from datetime import UTC, datetime

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_session
from app.core.security import create_access_token
from app.main import app
from app.models.action import ActionLog
from app.models.approval import ApprovalRequest
from app.models.assistant import Assistant
from app.models.task import TaskRun
from app.models.user import User


async def _make_user(session: AsyncSession) -> User:
    user = User(email=f"test-{uuid.uuid4()}@example.com")
    session.add(user)
    await session.flush()
    return user


async def _make_pending_approval(session: AsyncSession, user: User) -> tuple[ApprovalRequest, ActionLog]:
    assistant = Assistant(user_id=user.id, name="Test", role_type="youtube_moderator")
    session.add(assistant)
    await session.flush()

    task_run = TaskRun(
        assistant_id=assistant.id,
        status="waiting_approval",
        started_at=datetime.now(UTC),
    )
    session.add(task_run)
    await session.flush()

    action_log = ActionLog(
        task_run_id=task_run.id,
        action_type="youtube.comment.reply",
        status="pending_approval",
        input_data={"comment_id": "c1", "text": "Thanks!"},
    )
    session.add(action_log)
    await session.flush()

    approval_req = ApprovalRequest(
        action_log_id=action_log.id,
        requested_at=datetime.now(UTC),
        status="pending",
    )
    session.add(approval_req)
    await session.flush()

    return approval_req, action_log


@pytest.mark.asyncio
async def test_list_approvals_returns_pending(session: AsyncSession):
    user = await _make_user(session)
    approval_req, _ = await _make_pending_approval(session, user)

    app.dependency_overrides[get_async_session] = lambda: session
    token = create_access_token(str(user.id))
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
            resp = await c.get("/api/approvals", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        data = resp.json()
        assert any(item["id"] == str(approval_req.id) for item in data)
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_reject_approval(session: AsyncSession):
    user = await _make_user(session)
    approval_req, action_log = await _make_pending_approval(session, user)

    app.dependency_overrides[get_async_session] = lambda: session
    token = create_access_token(str(user.id))
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
            resp = await c.post(
                f"/api/approvals/{action_log.id}/reject",
                json={"reviewer_note": "Not needed"},
                headers={"Authorization": f"Bearer {token}"},
            )
        assert resp.status_code == 200
        assert resp.json()["status"] == "rejected"
        assert action_log.status == "rejected"
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_rollback_without_resource_id_fails(session: AsyncSession):
    user = await _make_user(session)
    _, action_log = await _make_pending_approval(session, user)
    action_log.status = "executed"
    # external_resource_id is NULL — SR-02 must reject this

    app.dependency_overrides[get_async_session] = lambda: session
    token = create_access_token(str(user.id))
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
            resp = await c.post(
                f"/api/approvals/{action_log.id}/rollback",
                headers={"Authorization": f"Bearer {token}"},
            )
        assert resp.status_code == 400
        assert "SR-02" in resp.json()["detail"]
    finally:
        app.dependency_overrides.clear()
