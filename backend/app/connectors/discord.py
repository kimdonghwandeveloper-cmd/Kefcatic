"""Discord connector (REST API v10).

For assistant use cases (reading/sending channel messages) Discord requires a
*bot* token, which does not expire — so there is no token-refresh step. The bot
token is provisioned out-of-band (Developer Portal) and stored as the connector's
access_token. The auth scheme defaults to "Bot" and is overridable via
config['auth_scheme'] (use "Bearer" for user-OAuth tokens).

Credentials dict keys:
  access_token  — Discord bot token (decrypted by ConnectorCredentialService)

Composite message IDs are formatted as 'channel_id:message_id'.
"""
from typing import Any

import httpx

from app.connectors.base import BaseConnector, ConnectorItem, register_connector
from app.connectors.oauth_helper import build_discord_auth_url, exchange_discord_code
from app.core.config import settings

_DISCORD_API = "https://discord.com/api/v10"

# Scopes for the install/authorize URL. `bot` installs the bot into a guild;
# identify/guilds support the user-auth side of the flow.
_SCOPES = ["bot", "identify", "guilds"]

# Bot gateway permissions bitfield: View Channels (1<<10) + Send Messages (1<<11)
# + Read Message History (1<<16).
_DEFAULT_PERMISSIONS = (1 << 10) | (1 << 11) | (1 << 16)

_DISCORD_REDIRECT_URI = "http://localhost:8000/api/connectors/discord/callback"


def build_auth_url(state: str) -> str:
    redirect_uri = getattr(settings, "discord_redirect_uri", _DISCORD_REDIRECT_URI)
    return build_discord_auth_url(_SCOPES, state, redirect_uri, _DEFAULT_PERMISSIONS)


async def exchange_code(code: str) -> dict:
    redirect_uri = getattr(settings, "discord_redirect_uri", _DISCORD_REDIRECT_URI)
    return await exchange_discord_code(code, redirect_uri)


@register_connector
class DiscordConnector(BaseConnector):
    connector_type = "discord"

    def _headers(self) -> dict[str, str]:
        scheme = self.config.get("auth_scheme", "Bot")
        return {"Authorization": f"{scheme} {self.credentials['access_token']}"}

    def _guild_id(self, override: str | None = None) -> str | None:
        return override or self.config.get("guild_id")

    async def validate_credentials(self) -> bool:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{_DISCORD_API}/users/@me",
                headers=self._headers(),
            )
            return resp.status_code == 200

    async def list_items(self, **kwargs: Any) -> list[ConnectorItem]:
        """List a channel's recent messages, or a guild's channels.

        kwargs:
          channel_id (str)  — if set, return that channel's messages
          guild_id (str)    — list channels of this guild (or config guild_id)
          max_results (int) — message limit, default 50 (max 100)
          before (str)      — message-ID cursor for pagination
        """
        if channel_id := kwargs.pop("channel_id", None):
            return await self._list_messages(channel_id, **kwargs)
        return await self._list_channels(**kwargs)

    async def _list_channels(self, **kwargs: Any) -> list[ConnectorItem]:
        guild_id = self._guild_id(kwargs.get("guild_id"))
        if not guild_id:
            raise ValueError("guild_id is required to list channels")

        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{_DISCORD_API}/guilds/{guild_id}/channels",
                headers=self._headers(),
            )
            resp.raise_for_status()
            channels = resp.json()

        return [
            ConnectorItem(
                id=ch["id"],
                content=ch.get("name", ""),
                metadata={
                    "name": ch.get("name", ""),
                    "type": ch.get("type"),
                    "guild_id": guild_id,
                    "topic": ch.get("topic", ""),
                },
                created_at="",
            )
            for ch in channels
        ]

    async def _list_messages(self, channel_id: str, **kwargs: Any) -> list[ConnectorItem]:
        params: dict[str, Any] = {"limit": kwargs.get("max_results", 50)}
        if before := kwargs.get("before"):
            params["before"] = before

        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{_DISCORD_API}/channels/{channel_id}/messages",
                headers=self._headers(),
                params=params,
            )
            resp.raise_for_status()
            messages = resp.json()

        return [_message_to_item(m, channel_id) for m in messages]

    async def read_item(self, item_id: str) -> ConnectorItem:
        """Read a single message. item_id is 'channel_id:message_id'."""
        channel_id, _, message_id = item_id.partition(":")
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{_DISCORD_API}/channels/{channel_id}/messages/{message_id}",
                headers=self._headers(),
            )
            resp.raise_for_status()
            message = resp.json()
        return _message_to_item(message, channel_id)

    async def create_item(self, data: dict) -> ConnectorItem:
        """Send a message to a channel.

        data keys:
          channel_id (str)  — target channel (required)
          content (str)     — message text (required)
        """
        channel_id = data["channel_id"]
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{_DISCORD_API}/channels/{channel_id}/messages",
                headers={**self._headers(), "Content-Type": "application/json"},
                json={"content": data["content"]},
            )
            resp.raise_for_status()
            message = resp.json()
        return _message_to_item(message, channel_id)

    async def update_item(self, item_id: str, data: dict) -> ConnectorItem:
        """Edit a message the bot authored. item_id is 'channel_id:message_id'."""
        channel_id, _, message_id = item_id.partition(":")
        async with httpx.AsyncClient() as client:
            resp = await client.patch(
                f"{_DISCORD_API}/channels/{channel_id}/messages/{message_id}",
                headers={**self._headers(), "Content-Type": "application/json"},
                json={"content": data["content"]},
            )
            resp.raise_for_status()
            message = resp.json()
        return _message_to_item(message, channel_id)

    async def delete_item(self, item_id: str) -> bool:
        """Delete a message. item_id is 'channel_id:message_id'."""
        channel_id, _, message_id = item_id.partition(":")
        async with httpx.AsyncClient() as client:
            resp = await client.delete(
                f"{_DISCORD_API}/channels/{channel_id}/messages/{message_id}",
                headers=self._headers(),
            )
        return resp.status_code in (200, 204)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _message_to_item(msg: dict, channel_id: str) -> ConnectorItem:
    author = msg.get("author", {})
    return ConnectorItem(
        id=f"{channel_id}:{msg.get('id', '')}",
        content=msg.get("content", ""),
        metadata={
            "channel_id": channel_id,
            "message_id": msg.get("id", ""),
            "author": author.get("username", ""),
            "author_id": author.get("id", ""),
            "is_bot": author.get("bot", False),
            "attachments": [a.get("url") for a in msg.get("attachments", [])],
        },
        created_at=msg.get("timestamp", ""),
    )
