"""Google Sheets API connector.

Spreadsheet discovery uses the Drive API; cell read/write uses the Sheets v4 API.

Credentials dict keys:
  access_token  — OAuth2 bearer token (decrypted by ConnectorCredentialService)
  refresh_token — OAuth2 refresh token

Required OAuth scopes:
  https://www.googleapis.com/auth/spreadsheets
  https://www.googleapis.com/auth/drive.readonly  (to list spreadsheets)
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

_SHEETS_API = "https://sheets.googleapis.com/v4/spreadsheets"
_DRIVE_API = "https://www.googleapis.com/drive/v3"

_SPREADSHEET_MIME = "application/vnd.google-apps.spreadsheet"

_SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.readonly",
]

_SHEETS_REDIRECT_URI = "http://localhost:8000/api/connectors/google-sheets/callback"


def build_auth_url(state: str) -> str:
    redirect_uri = getattr(settings, "sheets_redirect_uri", _SHEETS_REDIRECT_URI)
    return build_google_auth_url(_SCOPES, state, redirect_uri)


async def exchange_code(code: str) -> dict:
    redirect_uri = getattr(settings, "sheets_redirect_uri", _SHEETS_REDIRECT_URI)
    return await exchange_google_code(code, redirect_uri)


@register_connector
class GoogleSheetsConnector(BaseConnector):
    connector_type = "google_sheets"

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
        """List spreadsheets in the user's Drive.

        kwargs:
          max_results (int)  — default 20
          page_token (str)   — pagination token
          query (str)        — free-text filter on file name/content
        """
        q_parts = [f"mimeType = '{_SPREADSHEET_MIME}'", "trashed = false"]
        if query := kwargs.get("query"):
            q_parts.append(f"fullText contains '{query}'")

        params: dict[str, Any] = {
            "q": " and ".join(q_parts),
            "pageSize": kwargs.get("max_results", 20),
            "fields": "nextPageToken,files(id,name,createdTime,modifiedTime,webViewLink)",
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
                    "web_view_link": f.get("webViewLink"),
                    "modified_time": f.get("modifiedTime"),
                },
                created_at=f.get("createdTime", ""),
            )
            for f in data.get("files", [])
        ]

    async def read_item(self, item_id: str) -> ConnectorItem:
        """Read cell values from a spreadsheet.

        item_id is the spreadsheet ID. The range can be supplied via config
        ('range', e.g. 'Sheet1!A1:Z1000'); defaults to 'A1:Z1000'.
        """
        cell_range = self.config.get("range", "A1:Z1000")
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{_SHEETS_API}/{item_id}/values/{cell_range}",
                headers=await self._fresh_headers(),
            )
            resp.raise_for_status()
            data = resp.json()

        return ConnectorItem(
            id=item_id,
            content=data.get("values", []),
            metadata={
                "range": data.get("range", cell_range),
                "major_dimension": data.get("majorDimension", "ROWS"),
            },
            created_at="",
        )

    async def create_item(self, data: dict) -> ConnectorItem:
        """Append rows to a spreadsheet.

        data keys:
          spreadsheet_id (str)  — target spreadsheet (required)
          range (str)           — append anchor, default 'A1'
          values (list[list])   — rows to append (required)
        """
        spreadsheet_id = data["spreadsheet_id"]
        cell_range = data.get("range", "A1")
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{_SHEETS_API}/{spreadsheet_id}/values/{cell_range}:append",
                headers={**await self._fresh_headers(), "Content-Type": "application/json"},
                params={"valueInputOption": "USER_ENTERED", "insertDataOption": "INSERT_ROWS"},
                json={"values": data["values"]},
            )
            resp.raise_for_status()
            result = resp.json()

        updates = result.get("updates", {})
        return ConnectorItem(
            id=spreadsheet_id,
            content=data["values"],
            metadata={
                "updated_range": updates.get("updatedRange", ""),
                "updated_rows": updates.get("updatedRows", 0),
                "updated_cells": updates.get("updatedCells", 0),
            },
            created_at="",
        )

    async def update_item(self, item_id: str, data: dict) -> ConnectorItem:
        """Overwrite a cell range in a spreadsheet.

        item_id is the spreadsheet ID.
        data keys:
          range (str)         — A1 range to overwrite (required)
          values (list[list]) — replacement rows (required)
        """
        cell_range = data["range"]
        async with httpx.AsyncClient() as client:
            resp = await client.put(
                f"{_SHEETS_API}/{item_id}/values/{cell_range}",
                headers={**await self._fresh_headers(), "Content-Type": "application/json"},
                params={"valueInputOption": "USER_ENTERED"},
                json={"values": data["values"]},
            )
            resp.raise_for_status()
            result = resp.json()

        return ConnectorItem(
            id=item_id,
            content=data["values"],
            metadata={
                "updated_range": result.get("updatedRange", cell_range),
                "updated_cells": result.get("updatedCells", 0),
            },
            created_at="",
        )

    async def search(self, query: str, **kwargs: Any) -> list[ConnectorItem]:
        return await self.list_items(query=query, **kwargs)
