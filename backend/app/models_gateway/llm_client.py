from __future__ import annotations

from collections.abc import AsyncGenerator

from openai import AsyncOpenAI

from app.core.config import settings


class LLMClient:
    async def stream_chat(
        self,
        messages: list[dict[str, str]],
        temperature: float | None = None,
    ) -> AsyncGenerator[str, None]:
        raise NotImplementedError


class OpenAICompatibleLLMClient(LLMClient):
    def __init__(self) -> None:
        self._client = AsyncOpenAI(
            base_url=settings.model_base_url,
            api_key=settings.model_api_key,
        )
        self._model = settings.llm_model

    async def stream_chat(
        self,
        messages: list[dict[str, str]],
        temperature: float | None = None,
    ) -> AsyncGenerator[str, None]:
        request_payload = {
            "model": self._model,
            "messages": messages,
            "stream": True,
        }
        if temperature is not None:
            request_payload["temperature"] = temperature
        stream = await self._client.chat.completions.create(**request_payload)
        async for chunk in stream:
            delta = chunk.choices[0].delta.content
            if delta:
                yield delta


class FakeLLMClient(LLMClient):
    async def stream_chat(
        self,
        messages: list[dict[str, str]],
        temperature: float | None = None,
    ) -> AsyncGenerator[str, None]:
        _ = messages
        _ = temperature
        yield "LLM 未配置，返回占位答案。"


def build_llm_client() -> LLMClient:
    if settings.model_api_key:
        return OpenAICompatibleLLMClient()
    return FakeLLMClient()
