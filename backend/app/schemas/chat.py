from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.db.models.enums import MessageRole


class ChatSessionCreate(BaseModel):
    title: str | None = Field(default=None, max_length=255)
    kb_ids: list[UUID] = Field(default_factory=list)


class ChatSessionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    title: str | None
    kb_ids: list[str] | None
    is_archived: bool
    created_at: datetime
    updated_at: datetime


class ChatMessageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    session_id: UUID
    role: MessageRole
    content: str
    citations: list[dict] | None
    created_at: datetime


class ChatMessageListResponse(BaseModel):
    items: list[ChatMessageResponse]


class ChatStreamRequest(BaseModel):
    session_id: UUID | None = None
    question: str = Field(..., min_length=1, max_length=4000)
    kb_ids: list[UUID] = Field(default_factory=list)
    top_k: int | None = Field(default=None, ge=1, le=50)
    rerank_enabled: bool | None = None


class CitationItem(BaseModel):
    document_id: UUID
    document_name: str
    page_no: int | None
    chunk_id: UUID
    snippet: str


class ChatStreamEvent(BaseModel):
    type: Literal["delta", "citations", "done", "error"]
    content: str | None = None
    citations: list[CitationItem] | None = None
    session_id: UUID | None = None
    message_id: UUID | None = None
