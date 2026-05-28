from __future__ import annotations

from dataclasses import dataclass

from app.core.config import settings


@dataclass
class RerankResult:
    scores: list[float]


async def rerank_scores(query: str, documents: list[str]) -> RerankResult | None:
    if not settings.rerank_enabled:
        return None
    if not settings.model_api_key:
        return None
    return None
