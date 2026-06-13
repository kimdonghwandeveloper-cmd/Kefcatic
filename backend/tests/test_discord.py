"""Discord connector tests (httpx.MockTransport, no DB)."""
import json

import httpx
import pytest

from tests._connector_mock import patch_http, route


def _connector(monkeypatch, handler, config=None):
    captured = patch_http(monkeypatch, handler)
    from app.connectors.discord import DiscordConnector

    conn = DiscordConnector(credentials={"access_token": "bot-tok"}, config=config)
    return conn, captured


@pytest.mark.asyncio
async def test_validate_credentials(monkeypatch):
    conn, captured = _connector(monkeypatch, route({"/users/@me": {"json": {"id": "1", "username": "bot"}}}))
    assert await conn.validate_credentials() is True
    # default auth scheme is "Bot"
    assert captured[0].headers["Authorization"] == "Bot bot-tok"


@pytest.mark.asyncio
async def test_list_channels(monkeypatch):
    channels = [
        {"id": "C1", "name": "general", "type": 0, "topic": "hi"},
        {"id": "C2", "name": "random", "type": 0},
    ]
    conn, captured = _connector(monkeypatch, route({"/channels": {"json": channels}}), config={"guild_id": "G1"})
    items = await conn.list_items()
    assert [i.id for i in items] == ["C1", "C2"]
    assert items[0].metadata["name"] == "general"
    assert "/guilds/G1/channels" in str(captured[0].url)


@pytest.mark.asyncio
async def test_list_channels_requires_guild(monkeypatch):
    conn, _ = _connector(monkeypatch, route({}))
    with pytest.raises(ValueError, match="guild_id"):
        await conn.list_items()


@pytest.mark.asyncio
async def test_list_messages(monkeypatch):
    messages = [
        {"id": "M1", "content": "hello", "author": {"id": "U1", "username": "ann"}, "timestamp": "2026-06-13T00:00:00Z"},
        {"id": "M2", "content": "world", "author": {"id": "U2", "username": "bob"}},
    ]
    conn, captured = _connector(monkeypatch, route({"/messages": {"json": messages}}))
    items = await conn.list_items(channel_id="C1", max_results=10)
    assert items[0].id == "C1:M1"
    assert items[0].content == "hello"
    assert items[0].metadata["author"] == "ann"
    assert "/channels/C1/messages" in str(captured[0].url)


@pytest.mark.asyncio
async def test_send_message(monkeypatch):
    sent = {"id": "M9", "content": "ping", "author": {"id": "B1", "username": "bot", "bot": True}}
    conn, captured = _connector(monkeypatch, route({"/messages": {"json": sent}}))
    item = await conn.create_item({"channel_id": "C1", "content": "ping"})
    assert item.id == "C1:M9"
    assert captured[0].method == "POST"
    body = json.loads(captured[0].content)
    assert body == {"content": "ping"}


@pytest.mark.asyncio
async def test_delete_message(monkeypatch):
    def handler(req):
        assert "/channels/C1/messages/M9" in str(req.url)
        return httpx.Response(204)

    conn, captured = _connector(monkeypatch, handler)
    assert await conn.delete_item("C1:M9") is True
    assert captured[0].method == "DELETE"


@pytest.mark.asyncio
async def test_auth_scheme_override(monkeypatch):
    conn, captured = _connector(
        monkeypatch,
        route({"/users/@me": {"json": {"id": "1"}}}),
        config={"auth_scheme": "Bearer"},
    )
    await conn.validate_credentials()
    assert captured[0].headers["Authorization"] == "Bearer bot-tok"
