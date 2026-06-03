from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Enum, ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.models.enums import ChunkMethod, SubjectType, VisibilityScope
from app.db.models.mixins import TimestampMixin

if TYPE_CHECKING:
    from app.db.models.user import User


class KnowledgeBase(Base, TimestampMixin):
    __tablename__ = "knowledge_bases"
    __table_args__ = (
        UniqueConstraint(
            "name",
            "org_id",
            "visibility_scope",
            name="uq_kb_name_org_scope",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[str | None] = mapped_column(String(512), nullable=True)
    visibility_scope: Mapped[VisibilityScope] = mapped_column(
        Enum(VisibilityScope, name="visibility_scope"), nullable=False
    )
    org_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=True
    )
    owner_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    chunk_method: Mapped[ChunkMethod] = mapped_column(
        Enum(ChunkMethod, name="chunk_method"), nullable=False
    )
    chunk_size: Mapped[int] = mapped_column(default=1024, nullable=False)
    chunk_overlap: Mapped[int] = mapped_column(default=128, nullable=False)

    owner: Mapped["User | None"] = relationship(back_populates="knowledge_bases")


class KnowledgeBaseAcl(Base, TimestampMixin):
    __tablename__ = "kb_acl"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    kb_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("knowledge_bases.id"), nullable=False
    )
    subject_type: Mapped[SubjectType] = mapped_column(
        Enum(SubjectType, name="kb_subject_type"), nullable=False
    )
    subject_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    can_read: Mapped[bool] = mapped_column(default=True, nullable=False)
