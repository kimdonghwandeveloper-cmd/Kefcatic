"""Google Calendar API connector.

Credentials dict keys:
  access_token  — OAuth2 bearer token (decrypted by ConnectorCredentialService)
  refresh_token — OAuth2 refresh token

Required OAuth scopes:
  https://www.googleapis.com/auth/calendar
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

_CALENDAR_API = "https://www.googleapis.com/calendar/v3"

_SCOPES = [
    "https://www.googleapis.com/auth/calendar",
]

_CALENDAR_REDIRECT_URI = "http://localhost:8000/api/connectors/google-calendar/callback"


def build_auth_url(state: str) -> str:
    redirect_uri = getattr(settings, "calendar_redirect_uri", _CALENDAR_REDIRECT_URI)
    return build_google_auth_url(_SCOPES, state, redirect_uri)


async def exchange_code(code: str) -> dict:
    redirect_uri = getattr(settings, "calendar_redirect_uri", _CALENDAR_REDIRECT_URI)
    return await exchange_google_code(code, redirect_uri)


@register_connector
class GoogleCalendarConnector(BaseConnector):
    connector_type = "google_calendar"

    async def _fresh_headers(self) -> dict[str, str]:
        self.credentials = await ensure_fresh_token(self.credentials)
        return {"Authorization": f"Bearer {self.credentials['access_token']}"}

    def _calendar_id(self, override: str | None = None) -> str:
        return override or self.config.get("calendar_id", "primary")

    async def validate_credentials(self) -> bool:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{_CALENDAR_API}/users/me/calendarList",
                headers=await self._fresh_headers(),
                params={"maxResults": 1},
            )
            return resp.status_code == 200

    async def list_items(self, **kwargs: Any) -> list[ConnectorItem]:
        """List upcoming events from a calendar.

        kwargs:
          calendar_id (str)  — defaults to config or 'primary'
          max_results (int)  — default 20
          time_min (str)     — RFC3339 lower bound (inclusive)
          time_max (str)     — RFC3339 upper bound (exclusive)
          page_token (str)   — pagination token
          query (str)        — free-text search
        """
        calendar_id = self._calendar_id(kwargs.get("calendar_id"))
        params: dict[str, Any] = {
            "maxResults": kwargs.get("max_results", 20),
            "singleEvents": "true",
            "orderBy": "startTime",
        }
        if time_min := kwargs.get("time_min"):
            params["timeMin"] = time_min
        if time_max := kwargs.get("time_max"):
            params["timeMax"] = time_max
        if page_token := kwargs.get("page_token"):
            params["pageToken"] = page_token
        if query := kwargs.get("query"):
            params["q"] = query

        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{_CALENDAR_API}/calendars/{calendar_id}/events",
                headers=await self._fresh_headers(),
                params=params,
            )
            resp.raise_for_status()
            data = resp.json()

        return [_event_to_item(e, calendar_id) for e in data.get("items", [])]

    async def read_item(self, item_id: str) -> ConnectorItem:
        """Fetch a single event by ID."""
        calendar_id = self._calendar_id()
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{_CALENDAR_API}/calendars/{calendar_id}/events/{item_id}",
                headers=await self._fresh_headers(),
            )
            resp.raise_for_status()
            event = resp.json()
        return _event_to_item(event, calendar_id)

    async def create_item(self, data: dict) -> ConnectorItem:
        """Create a calendar event.

        data keys:
          summary (str)       — event title (required)
          start (dict|str)    — RFC3339 datetime or {dateTime|date, timeZone}
          end (dict|str)      — RFC3339 datetime or {dateTime|date, timeZone}
          description (str)   — optional body
          location (str)      — optional location
          attendees (list)   — optional list of email strings
          calendar_id (str)  — optional target calendar
        """
        calendar_id = self._calendar_id(data.get("calendar_id"))
        body = _build_event_body(data)
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{_CALENDAR_API}/calendars/{calendar_id}/events",
                headers={**await self._fresh_headers(), "Content-Type": "application/json"},
                json=body,
            )
            resp.raise_for_status()
            event = resp.json()
        return _event_to_item(event, calendar_id)

    async def update_item(self, item_id: str, data: dict) -> ConnectorItem:
        """Patch an existing event (partial update)."""
        calendar_id = self._calendar_id(data.get("calendar_id"))
        body = _build_event_body(data, partial=True)
        async with httpx.AsyncClient() as client:
            resp = await client.patch(
                f"{_CALENDAR_API}/calendars/{calendar_id}/events/{item_id}",
                headers={**await self._fresh_headers(), "Content-Type": "application/json"},
                json=body,
            )
            resp.raise_for_status()
            event = resp.json()
        return _event_to_item(event, calendar_id)

    async def delete_item(self, item_id: str) -> bool:
        """Delete an event. Returns True on success (HTTP 200/204)."""
        calendar_id = self._calendar_id()
        async with httpx.AsyncClient() as client:
            resp = await client.delete(
                f"{_CALENDAR_API}/calendars/{calendar_id}/events/{item_id}",
                headers=await self._fresh_headers(),
            )
        return resp.status_code in (200, 204)

    async def search(self, query: str, **kwargs: Any) -> list[ConnectorItem]:
        return await self.list_items(query=query, **kwargs)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _normalize_time(value: Any) -> dict:
    """Accept an RFC3339 string or a pre-built {dateTime|date} dict."""
    if isinstance(value, dict):
        return value
    return {"dateTime": value}


def _build_event_body(data: dict, partial: bool = False) -> dict:
    body: dict[str, Any] = {}
    if "summary" in data:
        body["summary"] = data["summary"]
    if "description" in data:
        body["description"] = data["description"]
    if "location" in data:
        body["location"] = data["location"]
    if "start" in data:
        body["start"] = _normalize_time(data["start"])
    if "end" in data:
        body["end"] = _normalize_time(data["end"])
    if attendees := data.get("attendees"):
        body["attendees"] = [
            a if isinstance(a, dict) else {"email": a} for a in attendees
        ]
    return body


def _event_to_item(event: dict, calendar_id: str) -> ConnectorItem:
    start = event.get("start", {})
    end = event.get("end", {})
    return ConnectorItem(
        id=event["id"],
        content={
            "summary": event.get("summary", "(제목 없음)"),
            "description": event.get("description", ""),
            "start": start.get("dateTime") or start.get("date", ""),
            "end": end.get("dateTime") or end.get("date", ""),
        },
        metadata={
            "calendar_id": calendar_id,
            "location": event.get("location", ""),
            "status": event.get("status", ""),
            "html_link": event.get("htmlLink", ""),
            "attendees": [a.get("email") for a in event.get("attendees", [])],
            "organizer": event.get("organizer", {}).get("email", ""),
        },
        created_at=event.get("created", ""),
    )
