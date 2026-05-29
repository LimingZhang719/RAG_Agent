from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.db.models.enums import RoleName


class LoginRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=64)
    password: str = Field(..., min_length=6, max_length=128)


class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=64)
    password: str = Field(..., min_length=6, max_length=128)
    email: str | None = Field(default=None, max_length=255)
    full_name: str | None = Field(default=None, max_length=128)
    role: RoleName
    org_id: UUID


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_at: datetime


class PendingApprovalResponse(BaseModel):
    status: str = "pending_approval"


class ApprovalUserResponse(BaseModel):
    id: UUID
    username: str
    email: str | None
    full_name: str | None
    org_id: UUID | None
    org_name: str | None
    roles: list[str]
    approval_status: str
    created_at: datetime


class UserResponse(BaseModel):
    id: UUID
    username: str
    email: str | None
    full_name: str | None
    org_id: UUID | None
    roles: list[str]
    is_active: bool
    approval_status: str
    last_login_at: datetime | None
