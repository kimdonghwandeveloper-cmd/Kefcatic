"""Gmail & Google Drive connector tests (httpx.MockTransport, no DB).

These complement the older monkeypatch-based tests with the robust transport
pattern shared across the connector suite.
"""
import base64
import json

import httpx
import pytest

from tests._connector_mock import patch_google_token, patch_http, route


# ── Gmail ─────────────────────────────────────────────────────────────────────

def _gmail(monkeypatch, handler):
    patch_google_token(monkeypatch, "gmail")
    captured = patch_http(monkeypatch, handler)
    from app.connectors.gmail import GmailConnector

    return GmailConnector(credentials={"access_token": "t", "refresh_token": "r"}), captured


@pytest.mark.asyncio
async def test_gmail_validate(monkeypatch):
    conn, _ = _gmail(monkeypatch, route({"/profile": {"json": {"messagesTotal": 3}}}))
    assert await conn.validate_credentials() is True


@pytest.mark.asyncio
async def test_gmail_read_item_decodes_body(monkeypatch):
    body_b64 = base64.urlsafe_b64encode(b"Hello World").decode()
    msg = {
        "id": "m1",
        "threadId": "t1",
        "labelIds": ["INBOX", "UNREAD"],
        "snippet": "Hello",
        "payload": {
            "mimeType": "text/plain",
            "headers": [
                {"name": "Subject", "value": "Hi"},
                {"name": "From", "value": "s@x.com"},
            ],
            "body": {"data": body_b64},
        },
    }
    conn, _ = _gmail(monkeypatch, route({"/messages/m1": {"json": msg}}))
    item = await conn.read_item("m1")
    assert item.content == "Hello World"
    assert item.metadata["subject"] == "Hi"


@pytest.mark.asyncio
async def test_gmail_create_draft(monkeypatch):
    conn, captured = _gmail(monkeypatch, route({"/drafts": {"json": {"id": "d1"}}}))
    item = await conn.create_item(
        {"to": "x@y.com", "subject": "S", "body": "B", "thread_id": "t1"}
    )
    assert item.id == "d1"
    assert captured[0].method == "POST"


# ── Google Drive ──────────────────────────────────────────────────────────────

def _drive(monkeypatch, handler):
    patch_google_token(monkeypatch, "google_drive")
    captured = patch_http(monkeypatch, handler)
    from app.connectors.google_drive import GoogleDriveConnector

    return GoogleDriveConnector(credentials={"access_token": "t", "refresh_token": "r"}), captured


@pytest.mark.asyncio
async def test_drive_list(monkeypatch):
    files = {"files": [{"id": "f1", "name": "doc", "mimeType": "application/pdf"}]}
    conn, _ = _drive(monkeypatch, route({"/files": {"json": files}}))
    items = await conn.list_items()
    assert items[0].id == "f1"


@pytest.mark.asyncio
async def test_drive_delete_moves_to_trash(monkeypatch):
    captured_body = {}

    def handler(req):
        captured_body["data"] = json.loads(req.content)
        captured_body["method"] = req.method
        return httpx.Response(200, json={"id": "f1", "trashed": True})

    conn, _ = _drive(monkeypatch, handler)
    assert await conn.delete_item("f1") is True
    assert captured_body["method"] == "PATCH"
    assert captured_body["data"] == {"trashed": True}
