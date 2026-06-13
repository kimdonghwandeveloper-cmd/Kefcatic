"""Slack connector (Web API).

Credentials dict keys:
  access_token  — Slack bot token (xoxb-...), decrypted by ConnectorCredentialService

Required bot scopes:
  channels:read, channels:history, chat:write, search:read, users:read

Slack Web API responses are always HTTP 200 with an {"ok": bool} envelope;
errors are surfaced via the "error" field, which this connector raises on.
"""
from typing import Any

import httpx

from app.connectors.base import BaseConnector, ConnectorItem, register_connector
from app.connectors.oauth_helper import build_slack_auth_url, exchange_slack_code
from app.core.config import settings

_SLACK_API = "https://slack.com/api"

_SCOPES = [
    "channels:read",
    "channels:history",
    "chat:write",
    "search:read",
    "users:read",
]

_SLACK_REDIRECT_URI = "http://localhost:8000/api/connectors/slack/callback"


def build_auth_url(state: str) -> str:
    redirect_uri = getattr(settings, "slack_redirect_uri", _SLACK_REDIRECT_URI)
    return build_slack_auth_url(_SCOPES, state, redirect_uri)


async def exchange_code(code: str) -> dict:
    redirect_uri = getattr(settings, "slack_redirect_uri", _SLACK_REDIRECT_URI)
    return await exchange_slack_code(code, redirect_uri)


@register_connector
class SlackConnector(BaseConnector):
    connector_type = "slack"

    def _headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.credentials['access_token']}"}

    @staticmethod
    def _unwrap(body: dict) -> dict:
        """Raise on a Slack error envelope, otherwise return the body."""
        if not body.get("ok"):
            raise ValueError(f"Slack API error: {body.get('error', 'unknown_error')}")
        return body

    async def validate_credentials(self) -> bool:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{_SLACK_API}/auth.test",
                headers=self._headers(),
            )
            return resp.status_code == 200 and resp.json().get("ok", False)

    async def list_items(self, **kwargs: Any) -> list[ConnectorItem]:
        """List channels, or messages within a channel if channel_id is given.

        kwargs:
          channel_id (str)   — if set, return that channel's messages
          max_results (int)  — default 50
          cursor (str)       — pagination cursor
        """
        if channel_id := kwargs.pop("channel_id", None):
            return await self._list_messages(channel_id, **kwargs)
        return await self._list_channels(**kwargs)

    async def _list_channels(self, **kwargs: Any) -> list[ConnectorItem]:
        params: dict[str, Any] = {
            "limit": kwargs.get("max_results", 50),
            "exclude_archived": "true",
            "types": "public_channel",
        }
        if cursor := kwargs.get("cursor"):
            params["cursor"] = cursor

        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{_SLACK_API}/conversations.list",
                headers=self._headers(),
                params=params,
            )
            resp.raise_for_status()
            body = self._unwrap(resp.json())

        return [
            ConnectorItem(
                id=ch["id"],
                content=ch.get("name", ""),
                metadata={
                    "name": ch.get("name", ""),
                    "is_private": ch.get("is_private", False),
                    "num_members": ch.get("num_members"),
                    "topic": (ch.get("topic") or {}).get("value", ""),
                },
                created_at=str(ch.get("created", "")),
            )
            for ch in body.get("channels", [])
        ]

    async def _list_messages(self, channel_id: str, **kwargs: Any) -> list[ConnectorItem]:
        params: dict[str, Any] = {
            "channel": channel_id,
            "limit": kwargs.get("max_results", 50),
        }
        if cursor := kwargs.get("cursor"):
            params["cursor"] = cursor

        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{_SLACK_API}/conversations.history",
                headers=self._headers(),
                params=params,
            )
            resp.raise_for_status()
            body = self._unwrap(resp.json())

        return [_message_to_item(m, channel_id) for m in body.get("messages", [])]

    async def read_item(self, item_id: str) -> ConnectorItem:
        """Read a message thread. item_id is 'channel_id:thread_ts'."""
        channel_id, _, thread_ts = item_id.partition(":")
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{_SLACK_API}/conversations.replies",
                headers=self._headers(),
                params={"channel": channel_id, "ts": thread_ts},
            )
            resp.raise_for_status()
            body = self._unwrap(resp.json())

        messages = body.get("messages", [])
        root = messages[0] if messages else {}
        item = _message_to_item(root, channel_id)
        item.metadata["reply_count"] = max(len(messages) - 1, 0)
        item.metadata["replies"] = [_message_to_item(m, channel_id).content for m in messages[1:]]
        return item

    async def create_item(self, data: dict) -> ConnectorItem:
        """Post a message to a channel.

        data keys:
          channel (str)    — channel ID or name (required)
          text (str)       — message text (required)
          thread_ts (str)  — optional parent message to reply under
        """
        payload: dict[str, Any] = {"channel": data["channel"], "text": data["text"]}
        if thread_ts := data.get("thread_ts"):
            payload["thread_ts"] = thread_ts

        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{_SLACK_API}/chat.postMessage",
                headers={**self._headers(), "Content-Type": "application/json; charset=utf-8"},
                json=payload,
            )
            resp.raise_for_status()
            body = self._unwrap(resp.json())

        return ConnectorItem(
            id=f"{body.get('channel')}:{body.get('ts')}",
            content=data["text"],
            metadata={"channel": body.get("channel"), "ts": body.get("ts")},
            created_at=str(body.get("ts", "")),
        )

    async def search(self, query: str, **kwargs: Any) -> list[ConnectorItem]:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{_SLACK_API}/search.messages",
                headers=self._headers(),
                params={"query": query, "count": kwargs.get("max_results", 20)},
            )
            resp.raise_for_status()
            body = self._unwrap(resp.json())

        matches = (body.get("messages") or {}).get("matches", [])
        return [_message_to_item(m, m.get("channel", {}).get("id", "")) for m in matches]


# ── Helpers ───────────────────────────────────────────────────────────────────

def _message_to_item(msg: dict, channel_id: str) -> ConnectorItem:
    ts = msg.get("ts", "")
    return ConnectorItem(
        id=f"{channel_id}:{ts}" if channel_id else ts,
        content=msg.get("text", ""),
        metadata={
            "channel": channel_id,
            "user": msg.get("user", ""),
            "ts": ts,
            "thread_ts": msg.get("thread_ts", ""),
            "type": msg.get("type", "message"),
        },
        created_at=ts,
    )
