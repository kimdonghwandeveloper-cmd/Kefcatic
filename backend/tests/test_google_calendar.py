"""Google Calendar connector tests (httpx.MockTransport, no DB)."""
import httpx
import pytest

from tests._connector_mock import patch_google_token, patch_http, route


def _connector(monkeypatch, handler):
    patch_google_token(monkeypatch, "google_calendar")
    captured = patch_http(monkeypatch, handler)
    from app.connectors.google_calendar import GoogleCalendarConnector

    conn = GoogleCalendarConnector(credentials={"access_token": "t", "refresh_token": "r"})
    return conn, captured


@pytest.mark.asyncio
async def test_validate_credentials(monkeypatch):
    conn, _ = _connector(monkeypatch, route({"calendarList": {"json": {"items": []}}}))
    assert await conn.validate_credentials() is True


@pytest.mark.asyncio
async def test_list_items(monkeypatch):
    events = {
        "items": [
            {
                "id": "evt1",
                "summary": "Standup",
                "start": {"dateTime": "2026-06-14T09:00:00Z"},
                "end": {"dateTime": "2026-06-14T09:15:00Z"},
                "htmlLink": "https://cal/evt1",
                "attendees": [{"email": "a@x.com"}],
                "status": "confirmed",
            }
        ]
    }
    conn, captured = _connector(monkeypatch, route({"/events": {"json": events}}))
    items = await conn.list_items(time_min="2026-06-14T00:00:00Z", max_results=10)

    assert len(items) == 1
    assert items[0].id == "evt1"
    assert items[0].content["summary"] == "Standup"
    assert items[0].metadata["attendees"] == ["a@x.com"]
    # primary calendar used by default; time_min forwarded
    assert "calendars/primary/events" in str(captured[0].url)
    assert "timeMin" in str(captured[0].url)


@pytest.mark.asyncio
async def test_create_item(monkeypatch):
    created = {
        "id": "new1",
        "summary": "Lunch",
        "start": {"dateTime": "2026-06-14T12:00:00Z"},
        "end": {"dateTime": "2026-06-14T13:00:00Z"},
        "status": "confirmed",
    }
    conn, captured = _connector(monkeypatch, route({"/events": {"json": created}}))
    item = await conn.create_item(
        {
            "summary": "Lunch",
            "start": "2026-06-14T12:00:00Z",
            "end": "2026-06-14T13:00:00Z",
            "attendees": ["b@x.com"],
        }
    )
    assert item.id == "new1"
    assert captured[0].method == "POST"
    import json
    body = json.loads(captured[0].content)
    assert body["start"] == {"dateTime": "2026-06-14T12:00:00Z"}
    assert body["attendees"] == [{"email": "b@x.com"}]


@pytest.mark.asyncio
async def test_update_item(monkeypatch):
    patched = {
        "id": "evt1",
        "summary": "Standup (updated)",
        "start": {"dateTime": "2026-06-14T09:30:00Z"},
        "end": {"dateTime": "2026-06-14T09:45:00Z"},
    }
    conn, captured = _connector(monkeypatch, route({"/events/evt1": {"json": patched}}))
    item = await conn.update_item("evt1", {"summary": "Standup (updated)"})
    assert item.content["summary"] == "Standup (updated)"
    assert captured[0].method == "PATCH"


@pytest.mark.asyncio
async def test_delete_item(monkeypatch):
    def handler(req):
        return httpx.Response(204)

    conn, captured = _connector(monkeypatch, handler)
    assert await conn.delete_item("evt1") is True
    assert captured[0].method == "DELETE"
