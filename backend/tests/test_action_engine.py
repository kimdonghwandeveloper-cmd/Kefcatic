"""Integration tests for the Action Engine approval gate (SR-01)."""
import uuid
from datetime import UTC, datetime

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.action import ActionLog
from app.models.assistant import Assistant
from app.models.policy import PermissionPolicy
from app.models.task import TaskRun
from app.models.user import User
from app.services.action_engine import execute_action


async def _setup(session: AsyncSession):
    user = User(email=f"test-{uuid.uuid4()}@example.com")
    session.add(user)
    await session.flush()

    assistant = Assistant(user_id=user.id, name="Test", role_type="youtube_moderator")
    session.add(assistant)
    await session.flush()

    task_run = TaskRun(
        assistant_id=assistant.id,
        status="running",
        started_at=datetime.now(UTC),
    )
    session.add(task_run)
    await session.flush()

    return user, assistant, task_run


@pytest.mark.asyncio
async def test_auto_mode_calls_handler(session: AsyncSession):
    _, assistant, task_run = await _setup(session)

    policy = PermissionPolicy(
        assistant_id=assistant.id,
        action_type="youtube.comment.list",
        approval_mode="auto",
        risk_level="low",
        is_reversible=False,
    )
    session.add(policy)
    await session.flush()

    called_with = {}

    async def fake_handler(data: dict) -> dict:
        called_with.update(data)
        return {"comments": []}

    result = await execute_action(
        session,
        task_run_id=task_run.id,
        action_type="youtube.comment.list",
        assistant_id=assistant.id,
        input_data={"max_results": 10},
        handler=fake_handler,
    )

    assert result.status == "executed"
    assert called_with.get("max_results") == 10


@pytest.mark.asyncio
async def test_disabled_mode_rejects(session: AsyncSession):
    _, assistant, task_run = await _setup(session)

    policy = PermissionPolicy(
        assistant_id=assistant.id,
        action_type="youtube.comment.hide",
        approval_mode="disabled",
        risk_level="high",
        is_reversible=True,
    )
    session.add(policy)
    await session.flush()

    result = await execute_action(
        session,
        task_run_id=task_run.id,
        action_type="youtube.comment.hide",
        assistant_id=assistant.id,
        input_data={"comment_id": "c1"},
    )

    assert result.status == "disabled"


@pytest.mark.asyncio
async def test_require_approval_creates_request(session: AsyncSession):
    _, assistant, task_run = await _setup(session)

    policy = PermissionPolicy(
        assistant_id=assistant.id,
        action_type="youtube.comment.reply",
        approval_mode="require_approval",
        risk_level="medium",
        is_reversible=True,
    )
    session.add(policy)
    await session.flush()

    result = await execute_action(
        session,
        task_run_id=task_run.id,
        action_type="youtube.comment.reply",
        assistant_id=assistant.id,
        input_data={"comment_id": "c1", "text": "Thank you!"},
    )

    assert result.status == "pending_approval"
    assert result.approval_request_id is not None


@pytest.mark.asyncio
async def test_draft_only_no_api_call(session: AsyncSession):
    _, assistant, task_run = await _setup(session)

    policy = PermissionPolicy(
        assistant_id=assistant.id,
        action_type="youtube.comment.reply",
        approval_mode="draft_only",
        risk_level="medium",
        is_reversible=True,
    )
    session.add(policy)
    await session.flush()

    handler_called = False

    async def handler(data: dict) -> dict:
        nonlocal handler_called
        handler_called = True
        return {}

    result = await execute_action(
        session,
        task_run_id=task_run.id,
        action_type="youtube.comment.reply",
        assistant_id=assistant.id,
        input_data={"comment_id": "c1", "text": "Draft"},
        handler=handler,
    )

    assert result.status == "draft"
    assert not handler_called


@pytest.mark.asyncio
async def test_sr04_no_duplicate_pending(session: AsyncSession):
    """SR-04: calling execute_action twice should return the same approval_request_id."""
    _, assistant, task_run = await _setup(session)

    policy = PermissionPolicy(
        assistant_id=assistant.id,
        action_type="youtube.comment.reply",
        approval_mode="require_approval",
        risk_level="medium",
        is_reversible=True,
    )
    session.add(policy)
    await session.flush()

    r1 = await execute_action(
        session,
        task_run_id=task_run.id,
        action_type="youtube.comment.reply",
        assistant_id=assistant.id,
        input_data={"comment_id": "c1", "text": "Hello"},
    )
    r2 = await execute_action(
        session,
        task_run_id=task_run.id,
        action_type="youtube.comment.reply",
        assistant_id=assistant.id,
        input_data={"comment_id": "c1", "text": "Hello"},
    )

    assert r1.approval_request_id == r2.approval_request_id
