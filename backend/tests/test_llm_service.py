"""Unit tests for LLM service — mocks the HTTP calls."""
import json

import httpx
import pytest

from app.services.llm_service import LLMService


def _make_anthropic_response(text: str) -> dict:
    return {"content": [{"type": "text", "text": text}]}


@pytest.mark.asyncio
async def test_classify_comment_parses_json(monkeypatch):
    payload = json.dumps({"category": "spam", "confidence": 0.95, "reasoning": "looks spammy"})

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=_make_anthropic_response(payload))

    import app.services.llm_service as llm_mod
    from app.core import config as cfg_mod

    monkeypatch.setattr(cfg_mod.settings, "anthropic_api_key", "test-key")
    monkeypatch.setattr(cfg_mod.settings, "openai_api_key", "")

    original = httpx.AsyncClient

    class Patched(httpx.AsyncClient):
        def __init__(self, **kwargs):
            kwargs["transport"] = httpx.MockTransport(handler)
            super().__init__(**kwargs)

    monkeypatch.setattr(httpx, "AsyncClient", Patched)

    svc = LLMService()
    result = await svc.classify_comment("Buy now!!!", ["spam", "positive"])

    assert result.category == "spam"
    assert result.confidence == 0.95


@pytest.mark.asyncio
async def test_generate_reply_draft(monkeypatch):
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=_make_anthropic_response("감사합니다!"))

    from app.core import config as cfg_mod
    monkeypatch.setattr(cfg_mod.settings, "anthropic_api_key", "test-key")
    monkeypatch.setattr(cfg_mod.settings, "openai_api_key", "")

    original = httpx.AsyncClient

    class Patched(httpx.AsyncClient):
        def __init__(self, **kwargs):
            kwargs["transport"] = httpx.MockTransport(handler)
            super().__init__(**kwargs)

    monkeypatch.setattr(httpx, "AsyncClient", Patched)

    svc = LLMService()
    draft = await svc.generate_reply_draft("영상 좋아요!")

    assert draft.text == "감사합니다!"
