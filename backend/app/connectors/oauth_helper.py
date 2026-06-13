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


# ── HubSpot OAuth2 ────────────────────────────────────────────────────────────
#
# HubSpot access tokens expire (~6h) and must be refreshed with the refresh token.

_HUBSPOT_AUTH_URI = "https://app.hubspot.com/oauth/authorize"
_HUBSPOT_TOKEN_URI = "https://api.hubapi.com/oauth/v1/token"


def build_hubspot_auth_url(scopes: list[str], state: str, redirect_uri: str) -> str:
    params = {
        "client_id": settings.hubspot_client_id,
        "redirect_uri": redirect_uri,
        "scope": " ".join(scopes),
        "state": state,
    }
    return f"{_HUBSPOT_AUTH_URI}?{urlencode(params)}"


async def exchange_hubspot_code(code: str, redirect_uri: str) -> dict:
    """Exchange an authorization code for HubSpot access + refresh tokens."""
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            _HUBSPOT_TOKEN_URI,
            data={
                "grant_type": "authorization_code",
                "client_id": settings.hubspot_client_id,
                "client_secret": settings.hubspot_client_secret,
                "redirect_uri": redirect_uri,
                "code": code,
            },
        )
        resp.raise_for_status()
        return resp.json()


async def refresh_hubspot_token(refresh_token: str) -> dict:
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            _HUBSPOT_TOKEN_URI,
            data={
                "grant_type": "refresh_token",
                "client_id": settings.hubspot_client_id,
                "client_secret": settings.hubspot_client_secret,
                "refresh_token": refresh_token,
            },
        )
        resp.raise_for_status()
        return resp.json()


async def ensure_fresh_hubspot_token(credentials: dict) -> dict:
    """Refresh the HubSpot access token if a probe shows it is invalid/expired.

    credentials must include 'refresh_token'.
    """
    async with httpx.AsyncClient() as client:
        probe = await client.get(
            f"https://api.hubapi.com/oauth/v1/access-tokens/{credentials.get('access_token', '')}",
        )
    if probe.status_code == 200:
        return credentials

    refreshed = await refresh_hubspot_token(credentials["refresh_token"])
    return {
        **credentials,
        "access_token": refreshed["access_token"],
        "refresh_token": refreshed.get("refresh_token", credentials["refresh_token"]),
    }


# ── Discord OAuth2 ────────────────────────────────────────────────────────────
#
# For assistant use cases (reading/sending channel messages) Discord requires a
# *bot* token, which does not expire — so no refresh step is needed. These helpers
# build the authorize/invite URL and exchange a user-auth code (identify/guilds);
# the bot token itself is provisioned out-of-band and stored as access_token.

_DISCORD_API = "https://discord.com/api/v10"
_DISCORD_AUTH_URI = "https://discord.com/oauth2/authorize"
_DISCORD_TOKEN_URI = "https://discord.com/api/oauth2/token"


def build_discord_auth_url(
    scopes: list[str], state: str, redirect_uri: str, permissions: int | None = None
) -> str:
    params = {
        "client_id": settings.discord_client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": " ".join(scopes),
        "state": state,
    }
    if permissions is not None:
        params["permissions"] = str(permissions)
    return f"{_DISCORD_AUTH_URI}?{urlencode(params)}"


async def exchange_discord_code(code: str, redirect_uri: str) -> dict:
    """Exchange an authorization code for Discord user tokens (identify/guilds)."""
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            _DISCORD_TOKEN_URI,
            data={
                "grant_type": "authorization_code",
                "client_id": settings.discord_client_id,
                "client_secret": settings.discord_client_secret,
                "redirect_uri": redirect_uri,
                "code": code,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        resp.raise_for_status()
        return resp.json()
