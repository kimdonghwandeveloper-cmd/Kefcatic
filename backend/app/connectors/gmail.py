"""Gmail API connector.

Credentials dict keys:
  access_token  — OAuth2 bearer token (decrypted by ConnectorCredentialService)
  refresh_token — OAuth2 refresh token

Required OAuth scopes:
  https://www.googleapis.com/auth/gmail.modify
"""
import base64
import email as email_lib
from typing import Any

import httpx

from app.connectors.base import BaseConnector, ConnectorItem, register_connector
from app.connectors.oauth_helper import (
    build_google_auth_url,
    ensure_fresh_token,
    exchange_google_code,
)
from app.core.config import settings

_GMAIL_API = "https://gmail.googleapis.com/gmail/v1/users/me"

_SCOPES = [
    "https://www.googleapis.com/auth/gmail.modify",
]

_GMAIL_REDIRECT_URI = "http://localhost:8000/api/connectors/gmail/callback"


def build_auth_url(state: str) -> str:
    redirect_uri = getattr(settings, "gmail_redirect_uri", _GMAIL_REDIRECT_URI)
    return build_google_auth_url(_SCOPES, state, redirect_uri)


async def exchange_code(code: str) -> dict:
    redirect_uri = getattr(settings, "gmail_redirect_uri", _GMAIL_REDIRECT_URI)
    return await exchange_google_code(code, redirect_uri)


@register_connector
class GmailConnector(BaseConnector):
    connector_type = "gmail"

    async def _fresh_headers(self) -> dict[str, str]:
        self.credentials = await ensure_fresh_token(self.credentials)
        return {"Authorization": f"Bearer {self.credentials['access_token']}"}

    async def validate_credentials(self) -> bool:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{_GMAIL_API}/profile",
                headers=await self._fresh_headers(),
            )
            return resp.status_code == 200

    async def list_items(self, **kwargs: Any) -> list[ConnectorItem]:
        """List unread messages from inbox.

        kwargs:
          max_results (int)  — default 20
          label_ids (list)   — default ['INBOX', 'UNREAD']
          page_token (str)   — pagination token
          query (str)        — Gmail search query
        """
        params: dict[str, Any] = {
            "maxResults": kwargs.get("max_results", 20),
            "labelIds": kwargs.get("label_ids", ["INBOX", "UNREAD"]),
        }
        if page_token := kwargs.get("page_token"):
            params["pageToken"] = page_token
        if query := kwargs.get("query"):
            params["q"] = query

        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{_GMAIL_API}/messages",
                headers=await self._fresh_headers(),
                params=params,
            )
            resp.raise_for_status()
            data = resp.json()

        message_ids = [m["id"] for m in data.get("messages", [])]
        items = []
        for msg_id in message_ids:
            item = await self.read_item(msg_id)
            items.append(item)
        return items

    async def read_item(self, item_id: str) -> ConnectorItem:
        """Fetch a single message with full payload."""
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{_GMAIL_API}/messages/{item_id}",
                headers=await self._fresh_headers(),
                params={"format": "full"},
            )
            resp.raise_for_status()
            msg = resp.json()

        headers = {h["name"].lower(): h["value"] for h in msg["payload"].get("headers", [])}
        body = _extract_body(msg["payload"])

        return ConnectorItem(
            id=msg["id"],
            content=body,
            metadata={
                "subject": headers.get("subject", "(제목 없음)"),
                "from": headers.get("from", ""),
                "to": headers.get("to", ""),
                "date": headers.get("date", ""),
                "thread_id": msg.get("threadId"),
                "label_ids": msg.get("labelIds", []),
                "snippet": msg.get("snippet", ""),
            },
            created_at=headers.get("date", ""),
        )

    async def create_item(self, data: dict) -> ConnectorItem:
        """Create a draft reply.

        data keys:
          thread_id (str)  — thread to reply to
          to (str)         — recipient email
          subject (str)    — email subject
          body (str)       — plain-text body
        """
        raw_message = _build_raw_message(
            to=data["to"],
            subject=data["subject"],
            body=data["body"],
            thread_id=data.get("thread_id"),
        )
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{_GMAIL_API}/drafts",
                headers={**await self._fresh_headers(), "Content-Type": "application/json"},
                json={"message": {"raw": raw_message, "threadId": data.get("thread_id")}},
            )
            resp.raise_for_status()
            draft = resp.json()

        return ConnectorItem(
            id=draft["id"],
            content=data["body"],
            metadata={"thread_id": data.get("thread_id"), "draft_id": draft["id"]},
            created_at="",
        )

    async def update_item(self, item_id: str, data: dict) -> ConnectorItem:
        """Apply a label change (e.g. mark as read).

        data keys:
          add_labels (list)     — label IDs to add
          remove_labels (list)  — label IDs to remove
        """
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{_GMAIL_API}/messages/{item_id}/modify",
                headers={**await self._fresh_headers(), "Content-Type": "application/json"},
                json={
                    "addLabelIds": data.get("add_labels", []),
                    "removeLabelIds": data.get("remove_labels", []),
                },
            )
            resp.raise_for_status()

        return await self.read_item(item_id)

    async def delete_item(self, item_id: str) -> bool:
        """Move a message to trash."""
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{_GMAIL_API}/messages/{item_id}/trash",
                headers=await self._fresh_headers(),
            )
        return resp.status_code == 200

    async def search(self, query: str, **kwargs: Any) -> list[ConnectorItem]:
        return await self.list_items(query=query, **kwargs)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _extract_body(payload: dict) -> str:
    """Recursively extract plain-text body from a Gmail message payload."""
    mime_type = payload.get("mimeType", "")
    if mime_type == "text/plain":
        data = payload.get("body", {}).get("data", "")
        return base64.urlsafe_b64decode(data + "==").decode("utf-8", errors="replace")
    for part in payload.get("parts", []):
        result = _extract_body(part)
        if result:
            return result
    return ""


def _build_raw_message(to: str, subject: str, body: str, thread_id: str | None) -> str:
    """Build a base64url-encoded RFC 2822 message."""
    msg = email_lib.message.EmailMessage()
    msg["To"] = to
    msg["Subject"] = subject
    if thread_id:
        msg["In-Reply-To"] = thread_id
    msg.set_content(body)
    return base64.urlsafe_b64encode(msg.as_bytes()).decode()
