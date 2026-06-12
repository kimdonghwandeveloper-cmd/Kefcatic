"""LLM service layer — abstracts OpenAI / Anthropic API calls.

Usage:
  service = LLMService()
  category = await service.classify_comment("좋은 영상이에요!", ["positive", "spam", "question"])
  draft = await service.generate_reply_draft("어디서 살 수 있나요?", context="쇼핑 채널")
"""
import json
from dataclasses import dataclass

import httpx

from app.core.config import settings


@dataclass
class ClassificationResult:
    category: str
    confidence: float
    reasoning: str


@dataclass
class ReplyDraft:
    text: str
    tokens_used: int


class LLMService:
    def __init__(self) -> None:
        self._provider = "anthropic" if settings.anthropic_api_key else "openai"

    async def classify_comment(
        self,
        comment_text: str,
        categories: list[str],
        system_context: str = "",
    ) -> ClassificationResult:
        """Classify a comment into one of the provided categories."""
        prompt = (
            f"댓글을 다음 카테고리 중 하나로 분류하세요: {', '.join(categories)}\n\n"
            f"댓글: {comment_text}\n\n"
            "JSON으로 응답하세요: {\"category\": \"...\", \"confidence\": 0.0~1.0, \"reasoning\": \"...\"}"
        )
        raw = await self._complete(system_context or "댓글 분류 전문가입니다.", prompt)
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            data = {"category": categories[0], "confidence": 0.5, "reasoning": raw}
        return ClassificationResult(
            category=data.get("category", categories[0]),
            confidence=float(data.get("confidence", 0.5)),
            reasoning=data.get("reasoning", ""),
        )

    async def generate_reply_draft(
        self,
        comment_text: str,
        context: str = "",
        style_guide: str = "",
        assistant_system_prompt: str = "",
    ) -> ReplyDraft:
        """Generate a reply draft for the given comment."""
        system = assistant_system_prompt or "친절하고 전문적인 크리에이터입니다."
        if style_guide:
            system += f"\n말투 지침: {style_guide}"

        prompt = (
            f"다음 댓글에 대한 답글 초안을 작성하세요.\n"
            f"{'컨텍스트: ' + context if context else ''}\n\n"
            f"댓글: {comment_text}\n\n"
            "자연스럽고 진심 어린 답글을 한 개만 작성하세요."
        )
        text = await self._complete(system, prompt)
        return ReplyDraft(text=text.strip(), tokens_used=0)

    async def _complete(self, system: str, user: str) -> str:
        if self._provider == "anthropic":
            return await self._anthropic_complete(system, user)
        return await self._openai_complete(system, user)

    async def _anthropic_complete(self, system: str, user: str) -> str:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": settings.anthropic_api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json={
                    "model": "claude-haiku-4-5-20251001",
                    "max_tokens": 512,
                    "system": system,
                    "messages": [{"role": "user", "content": user}],
                },
                timeout=30,
            )
            resp.raise_for_status()
            return resp.json()["content"][0]["text"]

    async def _openai_complete(self, system: str, user: str) -> str:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {settings.openai_api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "gpt-4o-mini",
                    "messages": [
                        {"role": "system", "content": system},
                        {"role": "user", "content": user},
                    ],
                    "max_tokens": 512,
                },
                timeout=30,
            )
            resp.raise_for_status()
            return resp.json()["choices"][0]["message"]["content"]
