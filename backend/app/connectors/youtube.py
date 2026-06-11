"""YouTube Data API v3 connector.

Credentials dict keys:
  access_token  — OAuth2 bearer token (decrypted by ConnectorCredentialService)
  refresh_token — OAuth2 refresh token
  token_uri     — https://oauth2.googleapis.com/token
  client_id     — Google OAuth client ID
  client_secret — Google OAuth client secret
"""
from typing import Any
from urllib.parse import urlencode

import httpx

from app.connectors.base import BaseConnector, ConnectorItem, register_connector
from app.core.config import settings

_YOUTUBE_API = "https://www.googleapis.com/youtube/v3"
_TOKEN_URI = "https://oauth2.googleapis.com/token"
_AUTH_URI = "https://accounts.google.com/o/oauth2/v2/auth"

_SCOPES = [
    "https://www.googleapis.com/auth/youtube.force-ssl",
]


def build_auth_url(state: str) -> str:
    params = {
        "client_id": settings.google_client_id,
        "redirect_uri": settings.google_redirect_uri,
        "response_type": "code",
        "scope": " ".join(_SCOPES),
        "access_type": "offline",
        "prompt": "consent",
        "state": state,
    }
    return f"{_AUTH_URI}?{urlencode(params)}"


async def exchange_code(code: str) -> dict:
    """Exchange an authorization code for access + refresh tokens."""
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            _TOKEN_URI,
            data={
                "code": code,
                "client_id": settings.google_client_id,
                "client_secret": settings.google_client_secret,
                "redirect_uri": settings.google_redirect_uri,
                "grant_type": "authorization_code",
            },
        )
        resp.raise_for_status()
        return resp.json()


async def refresh_access_token(refresh_token: str) -> dict:
    """Use the refresh token to obtain a new access token."""
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            _TOKEN_URI,
            data={
                "refresh_token": refresh_token,
                "client_id": settings.google_client_id,
                "client_secret": settings.google_client_secret,
                "grant_type": "refresh_token",
            },
        )
        resp.raise_for_status()
        return resp.json()


@register_connector
class YouTubeConnector(BaseConnector):
    connector_type = "youtube"

    def _headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.credentials['access_token']}"}

    async def validate_credentials(self) -> bool:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{_YOUTUBE_API}/channels",
                headers=self._headers(),
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
                headers=self._headers(),
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
                headers=self._headers(),
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
                headers={**self._headers(), "Content-Type": "application/json"},
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
                headers={**self._headers(), "Content-Type": "application/json"},
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
                headers=self._headers(),
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
                headers=self._headers(),
                params={"part": "id", "mine": "true"},
            )
            resp.raise_for_status()
            items = resp.json().get("items", [])
        if not items:
            raise ValueError("No YouTube channel found for this account")
        return items[0]["id"]
