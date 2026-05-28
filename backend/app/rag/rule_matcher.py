from __future__ import annotations

import re

from app.core.config import settings
from app.db.models.document import Chunk


def _tokenize(text: str) -> list[str]:
    tokens = re.split(r"\W+", text.lower())
    return [token for token in tokens if token]


def match_strong_rule(query: str, chunks: list[Chunk]) -> Chunk | None:
    query_lower = query.lower()
    query_tokens = set(_tokenize(query))

    for chunk in chunks:
        if not chunk.is_deterministic_rule:
            continue
        if chunk.rule_name:
            rule_name = chunk.rule_name.lower()
            if rule_name in query_lower:
                return chunk
            keywords = _tokenize(rule_name)
            if keywords:
                hits = sum(1 for token in keywords if token in query_tokens)
                if hits / len(keywords) >= settings.rule_match_threshold:
                    return chunk
    return None
