"""Smoke test: health endpoint returns 200 and db: connected."""
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_session
from app.main import app


@pytest.mark.asyncio
async def test_health_ok(session: AsyncSession) -> None:
    app.dependency_overrides[get_async_session] = lambda: session  # type: ignore[assignment]
    try:
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            resp = await client.get("/api/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert data["db"] == "connected"
    finally:
        app.dependency_overrides.clear()
