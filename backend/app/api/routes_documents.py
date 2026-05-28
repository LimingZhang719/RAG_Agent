from __future__ import annotations

import uuid
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import AppError
from app.core.security import get_current_user
from app.db.models.enums import DocumentStatus
from app.db.session import get_session
from app.schemas.document import (
    ChunkListResponse,
    ChunkResponse,
    DocumentListResponse,
    DocumentResponse,
)
from app.services.document_service import (
    clear_document_content,
    create_document,
    get_document,
    list_chunks,
    list_documents,
    mark_document_status,
)
from app.services.knowledge_base_service import get_knowledge_base
from app.storage.minio_client import MinioStorage
from app.workers.document_tasks import ingest_document_task

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("/upload", response_model=DocumentResponse)
async def upload_document(
    kb_id: UUID = Form(...),
    file: UploadFile = File(...),
    title: str | None = Form(default=None),
    session: AsyncSession = Depends(get_session),
    current_user=Depends(get_current_user),
) -> DocumentResponse:
    if file.filename is None:
        raise AppError("File name missing", status_code=400)

    kb = await get_knowledge_base(session, kb_id, current_user)

    file.file.seek(0, 2)
    size = file.file.tell()
    file.file.seek(0)
    max_bytes = settings.ingest_max_file_mb * 1024 * 1024
    if size > max_bytes:
        raise AppError("File too large", status_code=400)

    storage = MinioStorage()
    object_name = f"{kb_id}/{uuid.uuid4().hex}_{file.filename}"
    uploaded = storage.upload_fileobj(file.file, object_name, file.content_type)

    doc = await create_document(
        session=session,
        kb=kb,
        user=current_user,
        file_name=title or file.filename,
        file_uri=uploaded.file_uri,
        file_type=file.content_type or "application/octet-stream",
        size=uploaded.size,
    )

    ingest_document_task.delay(str(doc.id))

    return DocumentResponse.model_validate(doc)


@router.get("", response_model=DocumentListResponse)
async def list_document_items(
    kb_id: UUID,
    session: AsyncSession = Depends(get_session),
    current_user=Depends(get_current_user),
) -> DocumentListResponse:
    await get_knowledge_base(session, kb_id, current_user)
    docs = await list_documents(session, kb_id)
    return DocumentListResponse(
        items=[DocumentResponse.model_validate(doc) for doc in docs]
    )


@router.get("/{doc_id}", response_model=DocumentResponse)
async def get_document_detail(
    doc_id: UUID,
    session: AsyncSession = Depends(get_session),
    current_user=Depends(get_current_user),
) -> DocumentResponse:
    doc = await get_document(session, doc_id)
    await get_knowledge_base(session, doc.kb_id, current_user)
    return DocumentResponse.model_validate(doc)


@router.get("/{doc_id}/chunks", response_model=ChunkListResponse)
async def list_document_chunks(
    doc_id: UUID,
    session: AsyncSession = Depends(get_session),
    current_user=Depends(get_current_user),
) -> ChunkListResponse:
    doc = await get_document(session, doc_id)
    await get_knowledge_base(session, doc.kb_id, current_user)
    chunks = await list_chunks(session, doc_id)
    return ChunkListResponse(
        items=[ChunkResponse.model_validate(chunk) for chunk in chunks]
    )


@router.post("/{doc_id}/retry")
async def retry_document(
    doc_id: UUID,
    session: AsyncSession = Depends(get_session),
    current_user=Depends(get_current_user),
) -> dict[str, str]:
    doc = await get_document(session, doc_id)
    await get_knowledge_base(session, doc.kb_id, current_user)

    await clear_document_content(session, doc_id)
    await mark_document_status(session, doc_id, DocumentStatus.pending, None)
    ingest_document_task.delay(str(doc_id))
    return {"status": "queued"}
