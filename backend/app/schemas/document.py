from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.db.models.enums import DocumentStatus


class DocumentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    kb_id: UUID
    file_name: str
    file_uri: str
    file_type: str
    size: int
    status: DocumentStatus
    error_message: str | None
    created_by: UUID | None
    created_at: datetime
    updated_at: datetime


class DocumentListResponse(BaseModel):
    items: list[DocumentResponse]


class ChunkResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    document_id: UUID
    content: str
    content_hash: str
    page_no: int | None
    block_order: int | None
    section_path: str | None
    is_deterministic_rule: bool
    rule_name: str | None


class ChunkListResponse(BaseModel):
    items: list[ChunkResponse]
