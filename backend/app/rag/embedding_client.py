from __future__ import annotations

from dataclasses import dataclass

from openai import OpenAI

from app.core.config import settings


@dataclass
class EmbeddingConfig:
    model: str
    api_base: str
    api_key: str


class OpenAICompatibleEmbedding:
    def __init__(self, config: EmbeddingConfig) -> None:
        self._model = config.model
        self._client = OpenAI(base_url=config.api_base, api_key=config.api_key)

    def get_text_embedding_batch(self, texts: list[str], batch_size: int) -> list[list[float]]:
        embeddings: list[list[float]] = []
        for start in range(0, len(texts), batch_size):
            batch = texts[start : start + batch_size]
            response = self._client.embeddings.create(model=self._model, input=batch)
            embeddings.extend([item.embedding for item in response.data])
        return embeddings


def build_embedding_client() -> OpenAICompatibleEmbedding:
    api_base = settings.embedding_api_base or settings.model_base_url
    api_key = settings.embedding_api_key or settings.model_api_key
    return OpenAICompatibleEmbedding(
        EmbeddingConfig(
            model=settings.embedding_model,
            api_base=api_base,
            api_key=api_key,
        )
    )
