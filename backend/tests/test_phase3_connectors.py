"""Phase 3 connector tests — Gmail, Google Drive, oauth_helper.

Uses httpx.MockTransport so no real Google API calls are made.
"""
import pytest
import httpx

from app.connectors.base import ConnectorItem

# httpx.Response created without going through an actual transport has no
# `.request` attribute, which causes raise_for_status() to raise RuntimeError.
# Use this helper everywhere instead of constructing Response directly.
_DUMMY_REQ = httpx.Request("GET", "https://mock.test/")


def _mock_resp(status: int, **kwargs) -> httpx.Response:
    resp = httpx.Response(status, **kwargs)
    resp.request = _DUMMY_REQ
    return resp


# ── Mock transport helpers ────────────────────────────────────────────────────

def _make_transport(responses: dict[str, dict]) -> httpx.MockTransport:
    """Map URL substrings to mock response dicts {status_code, json}."""
    def handler(request: httpx.Request) -> httpx.Response:
        url = str(request.url)
        for key, resp in responses.items():
            if key in url:
                return _mock_resp(
                    resp.get("status_code", 200),
                    json=resp.get("json", {}),
                    text=resp.get("text"),
                )
        return _mock_resp(404, json={"error": "not found"})
    return httpx.MockTransport(handler)


# ── GmailConnector tests ──────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_gmail_list_items(monkeypatch):
    from app.connectors.gmail import GmailConnector

    messages_response = {
        "messages": [{"id": "msg1"}, {"id": "msg2"}],
        "nextPageToken": None,
    }
    msg_detail = {
        "id": "msg1",
        "threadId": "thread1",
        "labelIds": ["UNREAD", "INBOX"],
        "payload": {
            "headers": [
                {"name": "Subject", "value": "Test Subject"},
                {"name": "From", "value": "sender@example.com"},
                {"name": "Date", "value": "2026-06-12"},
            ],
            "mimeType": "text/plain",
            "body": {"data": "SGVsbG8gV29ybGQ="},  # "Hello World"
        },
    }

    calls = []

    async def mock_client_get(url, **kwargs):
        calls.append(url)
        if url.endswith("/messages"):
            return _mock_resp(200, json=messages_response)
        if "/messages/msg" in url:
            return _mock_resp(200, json=msg_detail)
        return _mock_resp(200, json={"access_token": "new_token", "expires_in": 3600})

    async def _noop(creds):
        return creds

    monkeypatch.setattr("app.connectors.gmail.ensure_fresh_token", _noop)

    connector = GmailConnector(
        credentials={"access_token": "tok", "refresh_token": "ref"},
    )

    # Patch the httpx.AsyncClient to use our mock
    class MockClient:
        async def __aenter__(self):
            return self
        async def __aexit__(self, *args):
            pass
        async def get(self, url, **kwargs):
            return await mock_client_get(url, **kwargs)

    monkeypatch.setattr("httpx.AsyncClient", MockClient)

    items = await connector.list_items(max_results=2)
    # Should return one item (msg1 is detailed, msg2 would also be fetched but mock returns same)
    assert len(items) >= 1
    assert items[0].id == "msg1"
    assert items[0].metadata["subject"] == "Test Subject"


@pytest.mark.asyncio
async def test_gmail_validate_credentials_success(monkeypatch):
    from app.connectors.gmail import GmailConnector

    async def _noop(c):
        return c

    monkeypatch.setattr("app.connectors.gmail.ensure_fresh_token", _noop)

    class MockClient:
        async def __aenter__(self):
            return self
        async def __aexit__(self, *args):
            pass
        async def get(self, url, **kwargs):
            return _mock_resp(200, json={"messagesTotal": 42})

    monkeypatch.setattr("httpx.AsyncClient", MockClient)

    connector = GmailConnector(credentials={"access_token": "tok", "refresh_token": "ref"})
    assert await connector.validate_credentials() is True


# ── GoogleDriveConnector tests ────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_drive_list_items(monkeypatch):
    from app.connectors.google_drive import GoogleDriveConnector

    async def _noop(c):
        return c

    monkeypatch.setattr("app.connectors.google_drive.ensure_fresh_token", _noop)

    files_response = {
        "files": [
            {
                "id": "file1",
                "name": "report.pdf",
                "mimeType": "application/pdf",
                "createdTime": "2026-06-01T00:00:00Z",
                "modifiedTime": "2026-06-01T00:00:00Z",
                "webViewLink": "https://drive.google.com/file/d/file1",
            }
        ]
    }

    class MockClient:
        async def __aenter__(self):
            return self
        async def __aexit__(self, *args):
            pass
        async def get(self, url, **kwargs):
            return _mock_resp(200, json=files_response)

    monkeypatch.setattr("httpx.AsyncClient", MockClient)

    connector = GoogleDriveConnector(credentials={"access_token": "tok", "refresh_token": "ref"})
    items = await connector.list_items(max_results=10)
    assert len(items) == 1
    assert items[0].id == "file1"
    assert items[0].metadata["name"] == "report.pdf"


@pytest.mark.asyncio
async def test_drive_read_google_doc(monkeypatch):
    from app.connectors.google_drive import GoogleDriveConnector

    async def _noop(c):
        return c

    monkeypatch.setattr("app.connectors.google_drive.ensure_fresh_token", _noop)

    meta = {
        "id": "doc1",
        "name": "My Doc",
        "mimeType": "application/vnd.google-apps.document",
        "createdTime": "2026-06-01T00:00:00Z",
    }

    class MockClient:
        async def __aenter__(self):
            return self
        async def __aexit__(self, *args):
            pass
        async def get(self, url, **kwargs):
            if "export" in url:
                return _mock_resp(200, text="Exported plain text content")
            return _mock_resp(200, json=meta)

    monkeypatch.setattr("httpx.AsyncClient", MockClient)

    connector = GoogleDriveConnector(credentials={"access_token": "tok", "refresh_token": "ref"})
    item = await connector.read_item("doc1")
    assert item.content == "Exported plain text content"
    assert item.metadata["mime_type"] == "application/vnd.google-apps.document"


# ── oauth_helper tests ────────────────────────────────────────────────────────

def test_build_google_auth_url():
    from app.connectors.oauth_helper import build_google_auth_url

    url = build_google_auth_url(
        scopes=["https://www.googleapis.com/auth/gmail.modify"],
        state="test_state",
        redirect_uri="http://localhost:8000/callback",
    )
    assert "accounts.google.com" in url
    assert "test_state" in url
    assert "gmail.modify" in url


@pytest.mark.asyncio
async def test_ensure_fresh_token_already_valid(monkeypatch):
    """If tokeninfo returns 200, no refresh should happen."""
    from app.connectors.oauth_helper import ensure_fresh_token

    class MockClient:
        async def __aenter__(self):
            return self
        async def __aexit__(self, *args):
            pass
        async def get(self, url, **kwargs):
            return _mock_resp(200, json={"expires_in": 3600})

    monkeypatch.setattr("httpx.AsyncClient", MockClient)

    creds = {"access_token": "valid_token", "refresh_token": "ref"}
    result = await ensure_fresh_token(creds)
    assert result["access_token"] == "valid_token"


@pytest.mark.asyncio
async def test_ensure_fresh_token_expired(monkeypatch):
    """If tokeninfo returns 400, should call refresh and return new token."""
    from app.connectors.oauth_helper import ensure_fresh_token

    call_count = {"get": 0, "post": 0}

    class MockClient:
        async def __aenter__(self):
            return self
        async def __aexit__(self, *args):
            pass
        async def get(self, url, **kwargs):
            call_count["get"] += 1
            return _mock_resp(400, json={"error": "invalid_token"})
        async def post(self, url, **kwargs):
            call_count["post"] += 1
            return _mock_resp(200, json={"access_token": "new_token", "expires_in": 3600})

    monkeypatch.setattr("httpx.AsyncClient", MockClient)

    creds = {"access_token": "expired_token", "refresh_token": "ref"}
    result = await ensure_fresh_token(creds)
    assert result["access_token"] == "new_token"
    assert call_count["post"] == 1
