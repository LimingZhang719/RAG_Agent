from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.db.models.enums import AgentRunStatus, AgentStepStatus


class AgentRunCreate(BaseModel):
    agent_type: str = Field(..., min_length=2, max_length=64)
    input: dict[str, Any] = Field(default_factory=dict)


class AgentRunResume(BaseModel):
    input: dict[str, Any] = Field(default_factory=dict)


class AgentRunResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    agent_type: str
    status: AgentRunStatus
    input: dict | None
    output: dict | None
    error_message: str | None
    started_at: datetime | None
    completed_at: datetime | None
    created_at: datetime
    updated_at: datetime


class AgentStepResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    run_id: UUID
    step_name: str
    status: AgentStepStatus
    input: dict | None
    output: dict | None
    error_message: str | None
    started_at: datetime | None
    completed_at: datetime | None
    created_at: datetime
    updated_at: datetime
