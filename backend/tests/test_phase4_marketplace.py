"""Phase 4 marketplace API tests."""
import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession

from app.main import app
from app.models.marketplace import MarketplaceTemplate
from app.models.user import User


@pytest.fixture
async def users(session: AsyncSession):
    author = User(email="author@test.com", display_name="Author")
    admin = User(email="admin@test.com", display_name="Admin", is_superuser=True)
    buyer = User(email="buyer@test.com", display_name="Buyer")
    session.add_all([author, admin, buyer])
    await session.flush()
    return {"author": author, "admin": admin, "buyer": buyer}


@pytest.fixture
async def approved_template(session, users):
    tpl = MarketplaceTemplate(
        author_id=users["author"].id,
        name="YouTube Moderator",
        description="Automate comment moderation",
        role_type="youtube_moderator",
        required_connectors=["youtube"],
        required_permissions=[
            "youtube.comment.list:auto",
            "youtube.comment.reply:require_approval",
            "youtube.comment.hide:always_manual",
        ],
        status="approved",
        version="1.0.0",
    )
    session.add(tpl)
    await session.flush()
    return tpl


def _auth(user: User, session=None):
    from app.core.deps import get_current_user, get_async_session
    app.dependency_overrides[get_current_user] = lambda: user
    if session is not None:
        app.dependency_overrides[get_async_session] = lambda: session


def _clear():
    app.dependency_overrides.clear()


# ── Browse ────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_list_approved_templates(session, approved_template):
    from app.core.deps import get_async_session
    app.dependency_overrides[get_async_session] = lambda: session
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get("/api/marketplace/templates")
        assert resp.status_code == 200
        assert any(t["name"] == "YouTube Moderator" for t in resp.json())
    finally:
        _clear()


@pytest.mark.asyncio
async def test_list_templates_filter_by_role_type(session, approved_template):
    from app.core.deps import get_async_session
    app.dependency_overrides[get_async_session] = lambda: session
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get("/api/marketplace/templates?role_type=youtube_moderator")
        assert resp.status_code == 200
        assert len(resp.json()) >= 1

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get("/api/marketplace/templates?role_type=nonexistent")
        assert resp.json() == []
    finally:
        _clear()


@pytest.mark.asyncio
async def test_get_template_detail(session, approved_template):
    from app.core.deps import get_async_session
    app.dependency_overrides[get_async_session] = lambda: session
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get(f"/api/marketplace/templates/{approved_template.id}")
        assert resp.status_code == 200
        assert resp.json()["name"] == "YouTube Moderator"
    finally:
        _clear()


@pytest.mark.asyncio
async def test_get_pending_template_returns_404(session, users):
    pending = MarketplaceTemplate(
        author_id=users["author"].id,
        name="Pending",
        required_connectors=[],
        required_permissions=[],
        status="pending",
    )
    session.add(pending)
    await session.flush()

    from app.core.deps import get_async_session
    app.dependency_overrides[get_async_session] = lambda: session
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get(f"/api/marketplace/templates/{pending.id}")
        assert resp.status_code == 404
    finally:
        _clear()


# ── Submit & Admin ────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_submit_template(session, users):
    _auth(users["author"], session)
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post("/api/marketplace/templates", json={
                "name": "Gmail Responder",
                "description": "Auto draft replies",
                "role_type": "gmail_responder",
                "required_connectors": ["gmail"],
                "required_permissions": ["gmail.draft.create:require_approval"],
            })
        assert resp.status_code == 201
        assert resp.json()["status"] == "pending"
    finally:
        _clear()


@pytest.mark.asyncio
async def test_admin_approve_template(session, users):
    pending = MarketplaceTemplate(
        author_id=users["author"].id,
        name="To Approve",
        required_connectors=[],
        required_permissions=[],
        status="pending",
    )
    session.add(pending)
    await session.flush()

    _auth(users["admin"], session)
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post(f"/api/marketplace/admin/templates/{pending.id}/approve", json={})
        assert resp.status_code == 200
        assert resp.json()["status"] == "approved"
    finally:
        _clear()


@pytest.mark.asyncio
async def test_admin_reject_template(session, users):
    pending = MarketplaceTemplate(
        author_id=users["author"].id,
        name="To Reject",
        required_connectors=[],
        required_permissions=[],
        status="pending",
    )
    session.add(pending)
    await session.flush()

    _auth(users["admin"], session)
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post(f"/api/marketplace/admin/templates/{pending.id}/reject", json={})
        assert resp.status_code == 200
        assert resp.json()["status"] == "rejected"
    finally:
        _clear()


@pytest.mark.asyncio
async def test_non_admin_cannot_approve(session, users, approved_template):
    _auth(users["buyer"], session)
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post(
                f"/api/marketplace/admin/templates/{approved_template.id}/approve", json={}
            )
        assert resp.status_code == 403
    finally:
        _clear()


# ── Install (SR-06) ───────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_install_sr06_missing_mode(session, users, approved_template):
    _auth(users["buyer"], session)
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post(
                f"/api/marketplace/templates/{approved_template.id}/install",
                json={
                    "approval_modes": {
                        "youtube.comment.list": "auto",
                        # missing youtube.comment.reply and youtube.comment.hide
                    }
                },
            )
        assert resp.status_code == 422
    finally:
        _clear()


@pytest.mark.asyncio
async def test_install_success(session, users, approved_template):
    _auth(users["buyer"], session)
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post(
                f"/api/marketplace/templates/{approved_template.id}/install",
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
        assert "assistant_id" in data
    finally:
        _clear()


# ── Reviews ───────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_create_and_list_review(session, users, approved_template):
    _auth(users["buyer"], session)
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post(
                f"/api/marketplace/templates/{approved_template.id}/reviews",
                json={"rating": 5, "comment": "Great template!"},
            )
            assert resp.status_code == 201
            assert resp.json()["rating"] == 5

            resp = await client.get(f"/api/marketplace/templates/{approved_template.id}/reviews")
            assert resp.status_code == 200
            assert len(resp.json()) == 1
    finally:
        _clear()


@pytest.mark.asyncio
async def test_duplicate_review_returns_409(session, users, approved_template):
    _auth(users["buyer"], session)
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            await client.post(
                f"/api/marketplace/templates/{approved_template.id}/reviews",
                json={"rating": 4},
            )
            resp = await client.post(
                f"/api/marketplace/templates/{approved_template.id}/reviews",
                json={"rating": 3},
            )
            assert resp.status_code == 409
    finally:
        _clear()
