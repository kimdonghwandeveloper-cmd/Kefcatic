"""Shared Google OAuth2 helpers used by all Google connectors (YouTube, Gmail, Drive).

All connectors share the same Google client_id/secret but request different scopes.
Token refresh is handled here so individual connectors don't duplicate that logic.
"""
from urllib.parse import urlencode

import httpx

from app.core.config import settings

_AUTH_URI = "https://accounts.google.com/o/oauth2/v2/auth"
_TOKEN_URI = "https://oauth2.googleapis.com/token"


def build_google_auth_url(scopes: list[str], state: str, redirect_uri: str) -> str:
    params = {
        "client_id": settings.google_client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": " ".join(scopes),
        "access_type": "offline",
        "prompt": "consent",
        "state": state,
    }
    return f"{_AUTH_URI}?{urlencode(params)}"


async def exchange_google_code(code: str, redirect_uri: str) -> dict:
    """Exchange an authorization code for access + refresh tokens."""
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            _TOKEN_URI,
            data={
                "code": code,
                "client_id": settings.google_client_id,
                "client_secret": settings.google_client_secret,
                "redirect_uri": redirect_uri,
                "grant_type": "authorization_code",
            },
        )
        resp.raise_for_status()
        return resp.json()


async def refresh_google_token(refresh_token: str) -> dict:
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


async def ensure_fresh_token(credentials: dict) -> dict:
    """Return credentials with a refreshed access_token if the current one is expired.

    The connector should call this before every API request.
    credentials must include 'refresh_token'.
    """
    import httpx as _httpx

    # Quick probe: try to call the tokeninfo endpoint
    async with _httpx.AsyncClient() as client:
        probe = await client.get(
            "https://oauth2.googleapis.com/tokeninfo",
            params={"access_token": credentials.get("access_token", "")},
        )
    if probe.status_code == 200:
        return credentials  # still valid

    # Token expired — refresh
    refreshed = await refresh_google_token(credentials["refresh_token"])
    return {**credentials, "access_token": refreshed["access_token"]}


# ── Slack OAuth2 ──────────────────────────────────────────────────────────────
#
# Slack uses its own OAuth endpoints. Classic bot tokens (xoxb-) do not expire,
# so no refresh step is required — exchange_slack_code returns the final token.

_SLACK_AUTH_URI = "https://slack.com/oauth/v2/authorize"
_SLACK_TOKEN_URI = "https://slack.com/api/oauth.v2.access"


def build_slack_auth_url(scopes: list[str], state: str, redirect_uri: str) -> str:
    params = {
        "client_id": settings.slack_client_id,
        "scope": ",".join(scopes),
        "redirect_uri": redirect_uri,
        "state": state,
    }
    return f"{_SLACK_AUTH_URI}?{urlencode(params)}"


async def exchange_slack_code(code: str, redirect_uri: str) -> dict:
    """Exchange an authorization code for a Slack bot token.

    Returns a normalized dict shaped like the Google flow so the connector
    storage path is uniform: {access_token, refresh_token, scope, team_id}.
    """
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            _SLACK_TOKEN_URI,
            data={
                "code": code,
                "client_id": settings.slack_client_id,
                "client_secret": settings.slack_client_secret,
                "redirect_uri": redirect_uri,
            },
        )
        resp.raise_for_status()
        body = resp.json()

    if not body.get("ok"):
        raise ValueError(f"Slack OAuth failed: {body.get('error', 'unknown_error')}")

    # Bot token lives under access_token; team metadata is kept for reference.
    return {
        "access_token": body.get("access_token", ""),
        "refresh_token": "",  # classic bot tokens do not expire
        "scope": body.get("scope", ""),
        "team_id": (body.get("team") or {}).get("id", ""),
        "bot_user_id": body.get("bot_user_id", ""),
    }
