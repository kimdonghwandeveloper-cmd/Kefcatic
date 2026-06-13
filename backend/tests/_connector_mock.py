"""Shared test helper for connector unit tests.

Uses httpx.MockTransport so requests are fully constructed (raise_for_status works)
and no real network calls are made. Patches the connector module's token-refresh
helper with an async passthrough.
"""
from __future__ import annotations

from typing import Callable

import httpx


def patch_http(monkeypatch, handler: Callable[[httpx.Request], httpx.Response]) -> list[httpx.Request]:
    """Route every httpx.AsyncClient request through `handler`.

    Returns a list that captures each Request for assertions.
    """
    captured: list[httpx.Request] = []

    def wrapped(request: httpx.Request) -> httpx.Response:
        captured.append(request)
        return handler(request)

    transport = httpx.MockTransport(wrapped)
    orig = httpx.AsyncClient

    def factory(*args, **kwargs):
        kwargs["transport"] = transport
        return orig(*args, **kwargs)

    monkeypatch.setattr("httpx.AsyncClient", factory)
    return captured


def patch_google_token(monkeypatch, module: str) -> None:
    """Replace `ensure_fresh_token` in a Google connector module with a no-op async."""
    async def fresh(creds):
        return creds

    monkeypatch.setattr(f"app.connectors.{module}.ensure_fresh_token", fresh)


def route(routes: dict[str, dict]) -> Callable[[httpx.Request], httpx.Response]:
    """Build a handler that matches URL substrings to {status_code, json} dicts.

    Iterates in insertion order; first substring match wins.
    """
    def handler(request: httpx.Request) -> httpx.Response:
        url = str(request.url)
        for key, resp in routes.items():
            if key in url:
                return httpx.Response(
                    status_code=resp.get("status_code", 200),
                    json=resp.get("json", {}),
                )
        return httpx.Response(404, json={"error": f"unmatched: {url}"})

    return handler
