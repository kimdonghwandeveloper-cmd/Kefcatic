"""Google Drive API connector.

Credentials dict keys:
  access_token  — OAuth2 bearer token (decrypted by ConnectorCredentialService)
  refresh_token — OAuth2 refresh token

Required OAuth scopes:
  https://www.googleapis.com/auth/drive.readonly
  https://www.googleapis.com/auth/documents.readonly  (for Docs export)
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

_DRIVE_API = "https://www.googleapis.com/drive/v3"
_DOCS_EXPORT = "https://docs.googleapis.com/v1/documents"

_SCOPES = [
    "https://www.googleapis.com/auth/drive.readonly",
    "https://www.googleapis.com/auth/documents.readonly",
]

_DRIVE_REDIRECT_URI = "http://localhost:8000/api/connectors/google-drive/callback"

# MIME types that can be exported as plain text
_EXPORTABLE = {
    "application/vnd.google-apps.document": "text/plain",
    "application/vnd.google-apps.spreadsheet": "text/csv",
}


def build_auth_url(state: str) -> str:
    redirect_uri = getattr(settings, "drive_redirect_uri", _DRIVE_REDIRECT_URI)
    return build_google_auth_url(_SCOPES, state, redirect_uri)


async def exchange_code(code: str) -> dict:
    redirect_uri = getattr(settings, "drive_redirect_uri", _DRIVE_REDIRECT_URI)
    return await exchange_google_code(code, redirect_uri)


@register_connector
class GoogleDriveConnector(BaseConnector):
    connector_type = "google_drive"

    async def _fresh_headers(self) -> dict[str, str]:
        self.credentials = await ensure_fresh_token(self.credentials)
        return {"Authorization": f"Bearer {self.credentials['access_token']}"}

    async def validate_credentials(self) -> bool:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{_DRIVE_API}/about",
                headers=await self._fresh_headers(),
                params={"fields": "user"},
            )
            return resp.status_code == 200

    async def list_items(self, **kwargs: Any) -> list[ConnectorItem]:
        """List files in Drive.

        kwargs:
          folder_id (str)    — restrict to a specific folder
          max_results (int)  — default 20
          page_token (str)   — pagination token
          query (str)        — Drive query string
          mime_type (str)    — filter by MIME type
        """
        q_parts = ["trashed = false"]
        if folder_id := kwargs.get("folder_id"):
            q_parts.append(f"'{folder_id}' in parents")
        if mime_type := kwargs.get("mime_type"):
            q_parts.append(f"mimeType = '{mime_type}'")
        if query := kwargs.get("query"):
            q_parts.append(f"fullText contains '{query}'")

        params: dict[str, Any] = {
            "q": " and ".join(q_parts),
            "pageSize": kwargs.get("max_results", 20),
            "fields": "nextPageToken,files(id,name,mimeType,createdTime,modifiedTime,size,webViewLink)",
        }
        if page_token := kwargs.get("page_token"):
            params["pageToken"] = page_token

        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{_DRIVE_API}/files",
                headers=await self._fresh_headers(),
                params=params,
            )
            resp.raise_for_status()
            data = resp.json()

        return [
            ConnectorItem(
                id=f["id"],
                content=f["name"],
                metadata={
                    "name": f["name"],
                    "mime_type": f.get("mimeType"),
                    "size": f.get("size"),
                    "web_view_link": f.get("webViewLink"),
                    "modified_time": f.get("modifiedTime"),
                },
                created_at=f.get("createdTime", ""),
            )
            for f in data.get("files", [])
        ]

    async def read_item(self, item_id: str) -> ConnectorItem:
        """Read file content. Google Docs/Sheets are exported as text/CSV."""
        # Get file metadata first
        async with httpx.AsyncClient() as client:
            meta_resp = await client.get(
                f"{_DRIVE_API}/files/{item_id}",
                headers=await self._fresh_headers(),
                params={"fields": "id,name,mimeType,createdTime,webViewLink"},
            )
            meta_resp.raise_for_status()
            meta = meta_resp.json()

        mime = meta.get("mimeType", "")
        content = ""

        if mime in _EXPORTABLE:
            # Export Google Workspace files as plain text
            export_mime = _EXPORTABLE[mime]
            async with httpx.AsyncClient() as client:
                export_resp = await client.get(
                    f"{_DRIVE_API}/files/{item_id}/export",
                    headers=await self._fresh_headers(),
                    params={"mimeType": export_mime},
                )
                if export_resp.status_code == 200:
                    content = export_resp.text
        elif not mime.startswith("application/vnd.google-apps"):
            # Binary files: just note them, don't download
            content = f"[Binary file: {meta['name']}]"

        return ConnectorItem(
            id=item_id,
            content=content,
            metadata={
                "name": meta["name"],
                "mime_type": mime,
                "web_view_link": meta.get("webViewLink"),
            },
            created_at=meta.get("createdTime", ""),
        )

    async def create_item(self, data: dict) -> ConnectorItem:
        """Create a new Google Doc with given title and content.

        data keys:
          title (str)   — document title
          content (str) — plain-text content
        """
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{_DRIVE_API}/files",
                headers={**await self._fresh_headers(), "Content-Type": "application/json"},
                json={
                    "name": data["title"],
                    "mimeType": "application/vnd.google-apps.document",
                },
            )
            resp.raise_for_status()
            file_meta = resp.json()

        return ConnectorItem(
            id=file_meta["id"],
            content=data.get("content", ""),
            metadata={"name": data["title"], "mime_type": "application/vnd.google-apps.document"},
            created_at="",
        )

    async def search(self, query: str, **kwargs: Any) -> list[ConnectorItem]:
        return await self.list_items(query=query, **kwargs)
