"""Phase 3 template API tests — SR-06 enforcement."""
import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession

from app.main import app
from app.models.assistant import Assistant
from app.models.user import User


@pytest.fixture
async def user(session: AsyncSession):
    u = User(email="tmpl@test.com", display_name="Template User")
    session.add(u)
    await session.flush()
    return u


@pytest.fixture
def auth_override(user):
    from app.core.deps import get_current_user
    app.dependency_overrides[get_current_user] = lambda: user
    yield
    app.dependency_overrides.clear()


@pytest.fixture
async def template(session, user):
    tpl = Assistant(
        user_id=user.id,
        name="YouTube Moderator",
        description="Template desc",
        role_type="youtube_moderator",
        config={
            "required_action_types": [
                "youtube.comment.list",
                "youtube.comment.reply",
                "youtube.comment.hide",
            ]
        },
        is_active=False,
        is_template=True,
    )
    session.add(tpl)
    await session.flush()
    return tpl


@pytest.mark.asyncio
async def test_list_templates(session, template, auth_override):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/api/assistants/templates")
        assert resp.status_code == 200
        names = [t["name"] for t in resp.json()]
        assert "YouTube Moderator" in names


@pytest.mark.asyncio
async def test_install_template_sr06_missing_modes(session, template, auth_override):
    """SR-06: missing approval_mode for a required action_type → 422."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post(
            f"/api/assistants/from-template/{template.id}",
            json={
                # only supplying 2 of the 3 required action types
                "approval_modes": {
                    "youtube.comment.list": "auto",
                    "youtube.comment.reply": "require_approval",
                    # youtube.comment.hide is missing
                }
            },
        )
        assert resp.status_code == 422
        assert "youtube.comment.hide" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_install_template_sr06_all_modes_provided(session, template, auth_override):
    """SR-06: all approval_modes supplied → creates assistant with user's modes."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post(
            f"/api/assistants/from-template/{template.id}",
            json={
                "name": "My YouTube Bot",
                "approval_modes": {
                    "youtube.comment.list": "auto",
                    "youtube.comment.reply": "require_approval",
                    "youtube.comment.hide": "always_manual",
                },
            },
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "My YouTube Bot"
        assert data["is_template"] is False


@pytest.mark.asyncio
async def test_install_template_not_found(session, auth_override):
    import uuid
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post(
            f"/api/assistants/from-template/{uuid.uuid4()}",
            json={"approval_modes": {}},
        )
        assert resp.status_code == 404


@pytest.mark.asyncio
async def test_save_as_template(session, user, auth_override):
    """User can save their own assistant as a template."""
    assistant = Assistant(
        user_id=user.id,
        name="My Custom Bot",
        role_type="gmail_responder",
        is_active=True,
        is_template=False,
    )
    session.add(assistant)
    await session.flush()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post(
            f"/api/assistants/{assistant.id}/save-as-template",
            json={"name": "Gmail Responder Template", "description": "My template"},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["is_template"] is True
        assert data["name"] == "Gmail Responder Template"
