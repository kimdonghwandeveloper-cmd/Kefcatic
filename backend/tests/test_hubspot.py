"""HubSpot connector tests (httpx.MockTransport, no DB)."""
import json

import pytest

from tests._connector_mock import patch_http, route


def _connector(monkeypatch, handler, config=None):
    captured = patch_http(monkeypatch, handler)

    async def fresh(creds):
        return creds

    monkeypatch.setattr("app.connectors.hubspot.ensure_fresh_hubspot_token", fresh)
    from app.connectors.hubspot import HubSpotConnector

    conn = HubSpotConnector(
        credentials={"access_token": "t", "refresh_token": "r"}, config=config
    )
    return conn, captured


@pytest.mark.asyncio
async def test_list_contacts(monkeypatch):
    body = {
        "results": [
            {
                "id": "101",
                "properties": {"email": "a@x.com", "firstname": "Ann"},
                "createdAt": "2026-01-01T00:00:00Z",
            }
        ]
    }
    conn, captured = _connector(monkeypatch, route({"/objects/contacts": {"json": body}}))
    items = await conn.list_items()
    assert items[0].id == "contacts:101"
    assert items[0].content["email"] == "a@x.com"
    assert "/objects/contacts" in str(captured[0].url)


@pytest.mark.asyncio
async def test_list_deals_via_kwarg(monkeypatch):
    body = {"results": [{"id": "55", "properties": {"dealname": "Big deal"}}]}
    conn, captured = _connector(monkeypatch, route({"/objects/deals": {"json": body}}))
    items = await conn.list_items(object_type="deals")
    assert items[0].id == "deals:55"
    assert items[0].metadata["object_type"] == "deals"


@pytest.mark.asyncio
async def test_create_contact(monkeypatch):
    body = {"id": "200", "properties": {"email": "new@x.com"}}
    conn, captured = _connector(monkeypatch, route({"/objects/contacts": {"json": body}}))
    item = await conn.create_item({"properties": {"email": "new@x.com"}})
    assert item.id == "contacts:200"
    assert captured[0].method == "POST"
    payload = json.loads(captured[0].content)
    assert payload == {"properties": {"email": "new@x.com"}}


@pytest.mark.asyncio
async def test_search(monkeypatch):
    body = {"results": [{"id": "9", "properties": {"email": "found@x.com"}}]}
    conn, captured = _connector(monkeypatch, route({"/search": {"json": body}}))
    items = await conn.search("found@x.com")
    assert items[0].id == "contacts:9"
    assert captured[0].method == "POST"
    payload = json.loads(captured[0].content)
    assert payload["query"] == "found@x.com"


@pytest.mark.asyncio
async def test_unsupported_object_raises(monkeypatch):
    conn, _ = _connector(monkeypatch, route({}))
    with pytest.raises(ValueError, match="Unsupported"):
        await conn.list_items(object_type="tickets")


@pytest.mark.asyncio
async def test_delete_with_prefixed_id(monkeypatch):
    import httpx

    def handler(req):
        assert "/objects/deals/55" in str(req.url)
        return httpx.Response(204)

    conn, captured = _connector(monkeypatch, handler)
    assert await conn.delete_item("deals:55") is True
    assert captured[0].method == "DELETE"
