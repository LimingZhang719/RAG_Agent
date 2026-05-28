from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.models.document import Chunk, Document
from app.db.models.enums import VisibilityScope
from app.db.models.user import User
from app.rag.embedding_client import build_embedding_client
from app.rag.rerankers import rerank_scores


@dataclass
class RetrievedChunk:
    chunk: Chunk
    document_name: str
    score: float
    vector_score: float | None
    keyword_score: float | None


def _visibility_filter(user: User):
    return or_(
        Chunk.visibility_scope == VisibilityScope.company,
        (Chunk.visibility_scope == VisibilityScope.department) & (Chunk.org_id == user.org_id),
        (Chunk.visibility_scope == VisibilityScope.personal) & (Chunk.owner_id == user.id),
    )


def _normalize_scores(scores: list[float]) -> list[float]:
    if not scores:
        return []
    max_score = max(scores)
    if max_score <= 0:
        return [0.0 for _ in scores]
    return [score / max_score for score in scores]


async def _vector_recall(
    session: AsyncSession,
    query_embedding: list[float],
    kb_ids: list[UUID],
    user: User,
    top_k: int,
) -> list[RetrievedChunk]:
    similarity = (1 - Chunk.embedding.cosine_distance(query_embedding)).label("score")
    result = await session.execute(
        select(Chunk, Document.file_name, similarity)
        .join(Document, Document.id == Chunk.document_id)
        .where(Chunk.embedding.isnot(None))
        .where(Chunk.kb_id.in_(kb_ids))
        .where(_visibility_filter(user))
        .order_by(similarity.desc())
        .limit(top_k)
    )
    items: list[RetrievedChunk] = []
    for chunk, file_name, score in result.all():
        items.append(
            RetrievedChunk(
                chunk=chunk,
                document_name=file_name,
                score=float(score or 0.0),
                vector_score=float(score or 0.0),
                keyword_score=None,
            )
        )
    return items


async def _keyword_recall(
    session: AsyncSession,
    query: str,
    kb_ids: list[UUID],
    user: User,
    top_k: int,
) -> list[RetrievedChunk]:
    tsvector = func.to_tsvector("simple", Chunk.content)
    tsquery = func.plainto_tsquery("simple", query)
    rank = func.ts_rank_cd(tsvector, tsquery).label("score")

    result = await session.execute(
        select(Chunk, Document.file_name, rank)
        .join(Document, Document.id == Chunk.document_id)
        .where(tsvector.op("@@")(tsquery))
        .where(Chunk.kb_id.in_(kb_ids))
        .where(_visibility_filter(user))
        .order_by(rank.desc())
        .limit(top_k)
    )

    items: list[RetrievedChunk] = []
    for chunk, file_name, score in result.all():
        items.append(
            RetrievedChunk(
                chunk=chunk,
                document_name=file_name,
                score=float(score or 0.0),
                vector_score=None,
                keyword_score=float(score or 0.0),
            )
        )
    return items


def _fuse_results(
    vector_hits: list[RetrievedChunk],
    keyword_hits: list[RetrievedChunk],
) -> list[RetrievedChunk]:
    fusion_method = settings.hybrid_fusion_method
    results: dict[UUID, RetrievedChunk] = {}

    if fusion_method == "rrf":
        k = 60
        for rank, item in enumerate(vector_hits, start=1):
            score = 1.0 / (k + rank)
            existing = results.get(item.chunk.id)
            if existing is None:
                results[item.chunk.id] = RetrievedChunk(
                    chunk=item.chunk,
                    document_name=item.document_name,
                    score=score,
                    vector_score=item.vector_score,
                    keyword_score=item.keyword_score,
                )
            else:
                existing.score += score
        for rank, item in enumerate(keyword_hits, start=1):
            score = 1.0 / (k + rank)
            existing = results.get(item.chunk.id)
            if existing is None:
                results[item.chunk.id] = RetrievedChunk(
                    chunk=item.chunk,
                    document_name=item.document_name,
                    score=score,
                    vector_score=item.vector_score,
                    keyword_score=item.keyword_score,
                )
            else:
                existing.score += score
    else:
        vector_scores = _normalize_scores([item.score for item in vector_hits])
        keyword_scores = _normalize_scores([item.score for item in keyword_hits])
        for item, score in zip(vector_hits, vector_scores):
            results[item.chunk.id] = RetrievedChunk(
                chunk=item.chunk,
                document_name=item.document_name,
                score=score * 0.6,
                vector_score=item.vector_score,
                keyword_score=item.keyword_score,
            )
        for item, score in zip(keyword_hits, keyword_scores):
            existing = results.get(item.chunk.id)
            if existing is None:
                results[item.chunk.id] = RetrievedChunk(
                    chunk=item.chunk,
                    document_name=item.document_name,
                    score=score * 0.4,
                    vector_score=item.vector_score,
                    keyword_score=item.keyword_score,
                )
            else:
                existing.score += score * 0.4
                existing.keyword_score = item.keyword_score

    return sorted(results.values(), key=lambda item: item.score, reverse=True)


async def retrieve_chunks(
    session: AsyncSession,
    query: str,
    kb_ids: list[UUID],
    user: User,
    top_k: int,
    rerank_enabled: bool | None = None,
) -> list[RetrievedChunk]:
    vector_hits: list[RetrievedChunk] = []
    has_embedding_key = bool(settings.embedding_api_key or settings.model_api_key)
    if has_embedding_key:
        embed_client = build_embedding_client()
        query_embedding = embed_client.get_text_embedding_batch([query], batch_size=1)[0]
        vector_hits = await _vector_recall(
            session, query_embedding, kb_ids, user, top_k
        )

    keyword_hits: list[RetrievedChunk] = []
    if settings.keyword_recall_enabled:
        keyword_hits = await _keyword_recall(
            session, query, kb_ids, user, settings.keyword_top_k
        )

    if keyword_hits:
        fused = _fuse_results(vector_hits, keyword_hits)
    else:
        fused = vector_hits
    filtered = [item for item in fused if item.score >= settings.rag_score_threshold]

    effective_rerank = settings.rerank_enabled if rerank_enabled is None else rerank_enabled
    if effective_rerank and filtered:
        rerank_candidates = filtered[: settings.rerank_top_k]
        rerank_result = await rerank_scores(
            query, [item.chunk.content for item in rerank_candidates]
        )
        if rerank_result and len(rerank_result.scores) == len(rerank_candidates):
            for item, score in zip(rerank_candidates, rerank_result.scores):
                item.score = score
            filtered = sorted(filtered, key=lambda item: item.score, reverse=True)

    return filtered[:top_k]
