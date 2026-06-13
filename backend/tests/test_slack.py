"""Slack connector tests (httpx.MockTransport, no DB)."""
import json

import pytest

from tests._connector_mock import patch_http, route


def _connector(monkeypatch, handler):
    captured = patch_http(monkeypatch, handler)
    from app.connectors.slack import SlackConnector

    conn = SlackConnector(credentials={"access_token": "xoxb-test"})
    return conn, captured


@pytest.mark.asyncio
async def test_validate_credentials(monkeypatch):
    conn, _ = _connector(monkeypatch, route({"auth.test": {"json": {"ok": True, "user": "bot"}}}))
    assert await conn.validate_credentials() is True


@pytest.mark.asyncio
async def test_validate_credentials_failure(monkeypatch):
    conn, _ = _connector(
        monkeypatch, route({"auth.test": {"json": {"ok": False, "error": "invalid_auth"}}})
    )
    assert await conn.validate_credentials() is False


@pytest.mark.asyncio
async def test_list_channels(monkeypatch):
    body = {
        "ok": True,
        "channels": [
            {"id": "C1", "name": "general", "num_members": 10, "created": 1700000000},
            {"id": "C2", "name": "random", "num_members": 5, "created": 1700000001},
        ],
    }
    conn, captured = _connector(monkeypatch, route({"conversations.list": {"json": body}}))
    items = await conn.list_items()
    assert [i.id for i in items] == ["C1", "C2"]
    assert items[0].metadata["name"] == "general"


@pytest.mark.asyncio
async def test_list_messages_in_channel(monkeypatch):
    body = {
        "ok": True,
        "messages": [
            {"ts": "1700.1", "text": "hello", "user": "U1", "type": "message"},
            {"ts": "1700.2", "text": "world", "user": "U2", "type": "message"},
        ],
    }
    conn, captured = _connector(monkeypatch, route({"conversations.history": {"json": body}}))
    items = await conn.list_items(channel_id="C1")
    assert items[0].id == "C1:1700.1"
    assert items[0].content == "hello"
    assert "channel=C1" in str(captured[0].url)


@pytest.mark.asyncio
async def test_post_message(monkeypatch):
    body = {"ok": True, "channel": "C1", "ts": "1700.9"}
    conn, captured = _connector(monkeypatch, route({"chat.postMessage": {"json": body}}))
    item = await conn.create_item({"channel": "C1", "text": "ping"})
    assert item.id == "C1:1700.9"
    assert captured[0].method == "POST"
    payload = json.loads(captured[0].content)
    assert payload == {"channel": "C1", "text": "ping"}


@pytest.mark.asyncio
async def test_post_message_error_raises(monkeypatch):
    body = {"ok": False, "error": "channel_not_found"}
    conn, _ = _connector(monkeypatch, route({"chat.postMessage": {"json": body}}))
    with pytest.raises(ValueError, match="channel_not_found"):
        await conn.create_item({"channel": "C9", "text": "x"})
