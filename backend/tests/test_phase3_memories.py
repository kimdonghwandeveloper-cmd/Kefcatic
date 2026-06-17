"""Phase 3 memory API tests."""
import uuid
import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession

from app.main import app
from app.models.assistant import Assistant
from app.models.user import User


@pytest.fixture
async def user_and_assistant(session: AsyncSession):
    user = User(email="mem@test.com", display_name="Mem User")
    session.add(user)
    await session.flush()

    assistant = Assistant(
        user_id=user.id,
        name="Test Assistant",
        is_active=True,
        is_template=False,
    )
    session.add(assistant)
    await session.flush()
    return user, assistant


@pytest.fixture
def auth_override(user_and_assistant, session):
    user, _ = user_and_assistant
    from app.core.deps import get_current_user, get_async_session
    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_async_session] = lambda: session
    yield
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_create_and_list_memory(session, user_and_assistant, auth_override):
    user, assistant = user_and_assistant
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Create
        resp = await client.post(
            f"/api/assistants/{assistant.id}/memories",
            json={"key": "user_name", "value": "김철수", "memory_type": "fact"},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["key"] == "user_name"
        assert data["value"] == "김철수"

        # List
        resp = await client.get(f"/api/assistants/{assistant.id}/memories")
        assert resp.status_code == 200
        items = resp.json()
        assert any(m["key"] == "user_name" for m in items)


@pytest.mark.asyncio
async def test_duplicate_key_returns_409(session, user_and_assistant, auth_override):
    user, assistant = user_and_assistant
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        await client.post(
            f"/api/assistants/{assistant.id}/memories",
            json={"key": "dup_key", "value": "v1"},
        )
        resp = await client.post(
            f"/api/assistants/{assistant.id}/memories",
            json={"key": "dup_key", "value": "v2"},
        )
        assert resp.status_code == 409


@pytest.mark.asyncio
async def test_update_memory(session, user_and_assistant, auth_override):
    user, assistant = user_and_assistant
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        await client.post(
            f"/api/assistants/{assistant.id}/memories",
            json={"key": "pref", "value": "formal"},
        )
        resp = await client.put(
            f"/api/assistants/{assistant.id}/memories/pref",
            json={"value": "casual"},
        )
        assert resp.status_code == 200
        assert resp.json()["value"] == "casual"


@pytest.mark.asyncio
async def test_delete_memory(session, user_and_assistant, auth_override):
    user, assistant = user_and_assistant
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        await client.post(
            f"/api/assistants/{assistant.id}/memories",
            json={"key": "del_key", "value": "gone"},
        )
        resp = await client.delete(f"/api/assistants/{assistant.id}/memories/del_key")
        assert resp.status_code == 204

        resp = await client.get(f"/api/assistants/{assistant.id}/memories/del_key")
        assert resp.status_code == 404
