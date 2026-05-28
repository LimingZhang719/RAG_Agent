from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.db.models.enums import ChunkMethod, VisibilityScope


class KnowledgeBaseCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=128)
    description: str | None = Field(default=None, max_length=512)
    visibility_scope: VisibilityScope
    org_id: UUID | None = None
    chunk_method: ChunkMethod = ChunkMethod.sentence
    chunk_size: int | None = Field(default=None, ge=200, le=4000)
    chunk_overlap: int | None = Field(default=None, ge=0, le=1000)


class KnowledgeBaseUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=128)
    description: str | None = Field(default=None, max_length=512)
    is_active: bool | None = None
    chunk_method: ChunkMethod | None = None
    chunk_size: int | None = Field(default=None, ge=200, le=4000)
    chunk_overlap: int | None = Field(default=None, ge=0, le=1000)


class KnowledgeBaseResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    description: str | None
    visibility_scope: VisibilityScope
    org_id: UUID | None
    owner_id: UUID | None
    is_active: bool
    chunk_method: ChunkMethod
    chunk_size: int
    chunk_overlap: int
    created_at: datetime
    updated_at: datetime
