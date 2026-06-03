from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.db.models.enums import SettingValueType


class SystemSettingUpsert(BaseModel):
    key: str = Field(..., min_length=2, max_length=128)
    value: Any = None
    value_type: SettingValueType = SettingValueType.string
    group_name: str = Field(..., min_length=2, max_length=64)
    description: str | None = None
    is_secret: bool = False
    is_runtime_editable: bool = True


class SystemSettingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    key: str
    value: Any = None
    value_type: SettingValueType
    group_name: str
    description: str | None
    is_secret: bool
    is_runtime_editable: bool
    updated_by: UUID | None
    created_at: datetime
    updated_at: datetime
