from __future__ import annotations

import json
import time
from collections.abc import AsyncGenerator
from typing import Any
from uuid import UUID

import logging

from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import AppError
from app.db.models.enums import MessageRole
from app.db.models.retrieval import RetrievalLog
from app.db.models.user import User
from app.rag.prompt_templates import build_messages
from app.rag.retrievers import RetrievedChunk, retrieve_chunks
from app.rag.rule_matcher import match_strong_rule
from app.services.chat_service import create_message, create_session, get_session
from app.services.knowledge_base_service import get_knowledge_base
from app.models_gateway.llm_client import build_llm_client

logger = logging.getLogger(__name__)

def _build_citations(chunks: list[RetrievedChunk]) -> list[dict[str, Any]]:
    citations: list[dict[str, Any]] = []
    for item in chunks:
        snippet = item.chunk.content[:300]
        citations.append(
            {
                "document_id": str(item.chunk.document_id),
                "document_name": item.document_name,
                "page_no": item.chunk.page_no,
                "chunk_id": str(item.chunk.id),
                "snippet": snippet,
            }
        )
    return citations


def _build_context(chunks: list[RetrievedChunk]) -> str:
    if not chunks:
        return ""
    lines: list[str] = []
    for idx, item in enumerate(chunks, start=1):
        content = item.chunk.content.strip().replace("\n", " ")
        lines.append(f"[{idx}] {content}")
    return "\n\n".join(lines)


def _serialize_event(payload: dict[str, Any]) -> str:
    data = json.dumps(payload, ensure_ascii=True)
    return f"data: {data}\n\n"


def _filter_kb_ids(kb_ids: list[UUID], session_kb_ids: list[str] | None) -> list[UUID]:
    if kb_ids:
        return kb_ids
    if not session_kb_ids:
        return []
    return [UUID(value) for value in session_kb_ids]


async def stream_chat(
    session: AsyncSession,
    user: User,
    question: str,
    kb_ids: list[UUID],
    session_id: UUID | None,
    top_k: int | None,
    rerank_enabled: bool | None,
) -> StreamingResponse:
    async def _event_stream() -> AsyncGenerator[str, None]:
        try:
            start_time = time.perf_counter()
            chat_session = None
            if session_id:
                chat_session = await get_session(session, session_id, user)
            resolved_kb_ids = _filter_kb_ids(
                kb_ids, chat_session.kb_ids if chat_session else None
            )
            if not resolved_kb_ids:
                raise AppError("Knowledge base ids required", status_code=400)

            for kb_id in resolved_kb_ids:
                await get_knowledge_base(session, kb_id, user)

            if chat_session is None:
                chat_session = await create_session(session, user, None, resolved_kb_ids)

            user_message = await create_message(
                session=session,
                session_id=chat_session.id,
                role=MessageRole.user,
                content=question,
                citations=None,
                created_by=user.id,
            )

            retrieved = await retrieve_chunks(
                session,
                question,
                resolved_kb_ids,
                user,
                top_k or settings.rag_top_k,
                rerank_enabled=rerank_enabled,
            )

            retrieved_sorted = sorted(
                retrieved,
                key=lambda item: (
                    str(item.chunk.document_id),
                    item.chunk.page_no or 0,
                    item.chunk.block_order or 0,
                ),
            )

            rule_chunk = match_strong_rule(question, [item.chunk for item in retrieved])
            citations = _build_citations(retrieved_sorted)

            yield _serialize_event(
                {
                    "type": "citations",
                    "citations": citations,
                }
            )

            answer_text = ""
            if rule_chunk is not None:
                answer_text = rule_chunk.content
                yield _serialize_event({"type": "delta", "content": answer_text})
            else:
                context = _build_context(retrieved_sorted)
                messages = build_messages(question, context)
                llm_client = build_llm_client()
                async for delta in llm_client.stream_chat(messages):
                    answer_text += delta
                    yield _serialize_event({"type": "delta", "content": delta})

            assistant_message = await create_message(
                session=session,
                session_id=chat_session.id,
                role=MessageRole.assistant,
                content=answer_text,
                citations=citations,
                created_by=user.id,
            )

            retrieved_payload = [
                {
                    "chunk_id": str(item.chunk.id),
                    "document_id": str(item.chunk.document_id),
                    "score": item.score,
                    "vector_score": item.vector_score,
                    "keyword_score": item.keyword_score,
                }
                for item in retrieved
            ]

            elapsed_ms = int((time.perf_counter() - start_time) * 1000)
            log = RetrievalLog(
                session_id=chat_session.id,
                message_id=user_message.id,
                query=question,
                retrieved_chunks=retrieved_payload,
                top_k=top_k or settings.rag_top_k,
                rerank_enabled=bool(rerank_enabled or settings.rerank_enabled),
                latency_ms=elapsed_ms,
            )
            session.add(log)
            await session.commit()

            yield _serialize_event(
                {
                    "type": "done",
                    "session_id": str(chat_session.id),
                    "message_id": str(assistant_message.id),
                }
            )
        except AppError as exc:
            logger.warning("Chat stream failed: %s", exc.message)
            yield _serialize_event({"type": "error", "content": exc.message})
        except Exception as exc:
            logger.exception("Unhandled chat stream error")
            message = str(exc) if settings.debug else "Internal error"
            yield _serialize_event({"type": "error", "content": message})

    return StreamingResponse(_event_stream(), media_type="text/event-stream")
