from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.db.models.enums import (
    AttachmentType,
    AuditResult,
    ExpenseApprovalAction,
    ExpenseStatus,
)


class ExpenseClaimCreate(BaseModel):
    title: str | None = Field(default=None, max_length=255)
    description: str | None = None
    total_amount: Decimal | None = Field(default=None, ge=0)
    currency: str = Field(default="CNY", max_length=8)
    city_tier: str | None = Field(default=None, max_length=32)


class ExpenseClaimUpdate(BaseModel):
    title: str | None = Field(default=None, max_length=255)
    description: str | None = None
    total_amount: Decimal | None = Field(default=None, ge=0)
    currency: str | None = Field(default=None, max_length=8)
    city_tier: str | None = Field(default=None, max_length=32)


class ExpenseAttachmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    claim_id: UUID
    file_uri: str
    file_name: str
    file_type: str
    size: int | None
    attachment_type: AttachmentType
    ocr_result: dict | None
    extracted_fields: dict | None
    ocr_confidence: Decimal | None
    classification_source: str | None
    created_at: datetime
    updated_at: datetime


class ExpenseAuditItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    claim_id: UUID
    name: str
    result: AuditResult
    evidence: str | None
    created_at: datetime
    updated_at: datetime


class ExpenseApprovalLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    claim_id: UUID
    actor_id: UUID
    action: ExpenseApprovalAction
    from_status: str | None
    to_status: str | None
    comment: str | None
    snapshot: dict | None
    created_at: datetime


class ExpenseClaimResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    status: ExpenseStatus
    claim_no: str | None
    expense_type: str
    title: str | None
    description: str | None
    total_amount: Decimal | None
    currency: str
    submitted_at: datetime | None
    approved_at: datetime | None
    audit_summary: dict | None
    reviewer_id: UUID | None
    reviewed_at: datetime | None
    review_comment: str | None
    created_at: datetime
    updated_at: datetime
    attachments: list[ExpenseAttachmentResponse] = Field(default_factory=list)
    audit_items: list[ExpenseAuditItemResponse] = Field(default_factory=list)


class ExpenseReviewAction(BaseModel):
    comment: str | None = Field(default=None, max_length=2000)


class TravelExpenseStandardCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=128)
    org_id: UUID | None = None
    city_tier: str | None = Field(default=None, max_length=32)
    daily_limit: Decimal | None = Field(default=None, ge=0)
    single_trip_limit: Decimal | None = Field(default=None, ge=0)
    currency: str = Field(default="CNY", max_length=8)
    effective_from: datetime | None = None
    effective_to: datetime | None = None
    is_active: bool = True
    metadata: dict[str, Any] | None = None


class TravelExpenseStandardResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: UUID
    name: str
    org_id: UUID | None
    city_tier: str | None
    daily_limit: Decimal | None
    single_trip_limit: Decimal | None
    currency: str
    effective_from: datetime | None
    effective_to: datetime | None
    is_active: bool
    metadata_: dict | None = None
    created_at: datetime
    updated_at: datetime
