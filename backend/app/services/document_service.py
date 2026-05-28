from __future__ import annotations

import uuid
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppError
from app.db.models.document import Document, DocumentBlock, Chunk
from app.db.models.enums import DocumentStatus
from app.db.models.knowledge_base import KnowledgeBase
from app.db.models.user import User


async def create_document(
    session: AsyncSession,
    kb: KnowledgeBase,
    user: User,
    file_name: str,
    file_uri: str,
    file_type: str,
    size: int,
) -> Document:
    doc = Document(
        id=uuid.uuid4(),
        kb_id=kb.id,
        file_name=file_name,
        file_uri=file_uri,
        file_type=file_type,
        size=size,
        status=DocumentStatus.pending,
        created_by=user.id,
        chunk_method=kb.chunk_method,
        chunk_size=kb.chunk_size,
        chunk_overlap=kb.chunk_overlap,
    )
    session.add(doc)
    await session.commit()
    await session.refresh(doc)
    return doc


async def list_documents(session: AsyncSession, kb_id: UUID) -> list[Document]:
    result = await session.execute(
        select(Document).where(Document.kb_id == kb_id).order_by(Document.created_at.desc())
    )
    return list(result.scalars().all())


async def list_chunks(session: AsyncSession, document_id: UUID) -> list[Chunk]:
    result = await session.execute(
        select(Chunk)
        .where(Chunk.document_id == document_id)
        .order_by(Chunk.block_order.asc())
    )
    return list(result.scalars().all())


async def get_document(session: AsyncSession, doc_id: UUID) -> Document:
    result = await session.execute(select(Document).where(Document.id == doc_id))
    doc = result.scalar_one_or_none()
    if doc is None:
        raise AppError("Document not found", status_code=404)
    return doc


async def mark_document_status(
    session: AsyncSession,
    document_id: UUID,
    status: DocumentStatus,
    error_message: str | None = None,
) -> None:
    doc = await get_document(session, document_id)
    doc.status = status
    doc.error_message = error_message
    await session.commit()


async def clear_document_content(session: AsyncSession, document_id: UUID) -> None:
    await session.execute(
        delete(DocumentBlock).where(DocumentBlock.document_id == document_id)
    )
    await session.execute(delete(Chunk).where(Chunk.document_id == document_id))
    await session.commit()


async def update_document_chunking(
    session: AsyncSession,
    document_id: UUID,
    chunk_method,
    chunk_size: int,
    chunk_overlap: int,
) -> Document:
    doc = await get_document(session, document_id)
    doc.chunk_method = chunk_method
    doc.chunk_size = chunk_size
    doc.chunk_overlap = chunk_overlap
    await session.commit()
    await session.refresh(doc)
    return doc
