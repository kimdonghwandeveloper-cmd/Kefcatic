"""YouTube Data API v3 connector.

Credentials dict keys:
  access_token  — OAuth2 bearer token (decrypted by ConnectorCredentialService)
  refresh_token — OAuth2 refresh token
"""
from typing import Any

import httpx

from app.connectors.base import BaseConnector, ConnectorItem, register_connector
from app.connectors.oauth_helper import (
    build_google_auth_url,
    ensure_fresh_token,
    exchange_google_code,
)
from app.core.config import settings

_YOUTUBE_API = "https://www.googleapis.com/youtube/v3"

_SCOPES = [
    "https://www.googleapis.com/auth/youtube.force-ssl",
]


def build_auth_url(state: str) -> str:
    return build_google_auth_url(_SCOPES, state, settings.google_redirect_uri)


async def exchange_code(code: str) -> dict:
    return await exchange_google_code(code, settings.google_redirect_uri)


@register_connector
class YouTubeConnector(BaseConnector):
    connector_type = "youtube"

    async def _fresh_headers(self) -> dict[str, str]:
        self.credentials = await ensure_fresh_token(self.credentials)
        return {"Authorization": f"Bearer {self.credentials['access_token']}"}

    async def validate_credentials(self) -> bool:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{_YOUTUBE_API}/channels",
                headers=await self._fresh_headers(),
                params={"part": "id", "mine": "true"},
            )
            return resp.status_code == 200

    async def list_items(self, **kwargs: Any) -> list[ConnectorItem]:
        """List comment threads for the authenticated channel.

        kwargs:
          video_id (str)      — filter by video
          max_results (int)   — default 20, max 100
          page_token (str)    — pagination token
        """
        params: dict[str, Any] = {
            "part": "snippet,replies",
            "maxResults": kwargs.get("max_results", 20),
            "order": "time",
        }
        if video_id := kwargs.get("video_id"):
            params["videoId"] = video_id
        else:
            params["allThreadsRelatedToChannelId"] = await self._get_channel_id()
        if page_token := kwargs.get("page_token"):
            params["pageToken"] = page_token

        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{_YOUTUBE_API}/commentThreads",
                headers=await self._fresh_headers(),
                params=params,
            )
            resp.raise_for_status()
            data = resp.json()

        items = []
        for item in data.get("items", []):
            snippet = item["snippet"]["topLevelComment"]["snippet"]
            items.append(
                ConnectorItem(
                    id=item["id"],
                    content=snippet.get("textDisplay", ""),
                    metadata={
                        "author": snippet.get("authorDisplayName"),
                        "like_count": snippet.get("likeCount", 0),
                        "video_id": snippet.get("videoId"),
                        "reply_count": item["snippet"].get("totalReplyCount", 0),
                    },
                    created_at=snippet.get("publishedAt", ""),
                )
            )
        return items

    async def read_item(self, item_id: str) -> ConnectorItem:
        """Fetch a single comment thread by ID."""
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{_YOUTUBE_API}/commentThreads",
                headers=await self._fresh_headers(),
                params={"part": "snippet,replies", "id": item_id},
            )
            resp.raise_for_status()
            items = resp.json().get("items", [])

        if not items:
            raise ValueError(f"Comment thread {item_id} not found")
        item = items[0]
        snippet = item["snippet"]["topLevelComment"]["snippet"]
        return ConnectorItem(
            id=item["id"],
            content=snippet.get("textDisplay", ""),
            metadata={
                "author": snippet.get("authorDisplayName"),
                "like_count": snippet.get("likeCount", 0),
                "video_id": snippet.get("videoId"),
                "reply_count": item["snippet"].get("totalReplyCount", 0),
            },
            created_at=snippet.get("publishedAt", ""),
        )

    async def create_item(self, data: dict) -> ConnectorItem:
        """Post a reply to a comment thread.

        data keys:
          comment_id (str) — parent comment thread ID
          text (str)       — reply text
        """
        body = {
            "snippet": {
                "parentId": data["comment_id"],
                "textOriginal": data["text"],
            }
        }
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{_YOUTUBE_API}/comments",
                headers={**await self._fresh_headers(), "Content-Type": "application/json"},
                params={"part": "snippet"},
                json=body,
            )
            resp.raise_for_status()
            item = resp.json()

        snippet = item["snippet"]
        return ConnectorItem(
            id=item["id"],
            content=snippet.get("textDisplay", ""),
            metadata={"parent_id": snippet.get("parentId")},
            created_at=snippet.get("publishedAt", ""),
        )

    async def update_item(self, item_id: str, data: dict) -> ConnectorItem:
        """Update the text of an existing comment.

        data keys:
          text (str) — new comment text
        """
        body = {"id": item_id, "snippet": {"textOriginal": data["text"]}}
        async with httpx.AsyncClient() as client:
            resp = await client.put(
                f"{_YOUTUBE_API}/comments",
                headers={**await self._fresh_headers(), "Content-Type": "application/json"},
                params={"part": "snippet"},
                json=body,
            )
            resp.raise_for_status()
            item = resp.json()

        snippet = item["snippet"]
        return ConnectorItem(
            id=item["id"],
            content=snippet.get("textDisplay", ""),
            metadata={},
            created_at=snippet.get("publishedAt", ""),
        )

    async def delete_item(self, item_id: str) -> bool:
        """Set a comment's moderation status to 'rejected' (hides it)."""
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{_YOUTUBE_API}/comments/setModerationStatus",
                headers=await self._fresh_headers(),
                params={
                    "id": item_id,
                    "moderationStatus": "rejected",
                    "banAuthor": "false",
                },
            )
        return resp.status_code == 204

    async def _get_channel_id(self) -> str:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{_YOUTUBE_API}/channels",
                headers=await self._fresh_headers(),
                params={"part": "id", "mine": "true"},
            )
            resp.raise_for_status()
            items = resp.json().get("items", [])
        if not items:
            raise ValueError("No YouTube channel found for this account")
        return items[0]["id"]
