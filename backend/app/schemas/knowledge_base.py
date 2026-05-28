from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.db.models.enums import VisibilityScope


class KnowledgeBaseCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=128)
    description: str | None = Field(default=None, max_length=512)
    visibility_scope: VisibilityScope
    org_id: UUID | None = None


class KnowledgeBaseUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=128)
    description: str | None = Field(default=None, max_length=512)
    is_active: bool | None = None


class KnowledgeBaseResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    description: str | None
    visibility_scope: VisibilityScope
    org_id: UUID | None
    owner_id: UUID | None
    is_active: bool
    created_at: datetime
    updated_at: datetime
