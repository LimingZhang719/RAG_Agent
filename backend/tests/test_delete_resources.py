from __future__ import annotations

import uuid

import pytest
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.exceptions import AppError
from app.core.security import hash_password
from app.db.models.document import Chunk, Document, DocumentBlock
from app.db.models.enums import (
    BlockType,
    ChunkMethod,
    DocumentStatus,
    RoleName,
    SubjectType,
    VisibilityScope,
)
from app.db.models.knowledge_base import KnowledgeBase, KnowledgeBaseAcl
from app.db.models.organization import Organization
from app.db.models.role import Role
from app.db.models.user import User
from app.db.models.user_role import UserRole
from app.services.document_service import delete_document
from app.services.knowledge_base_service import delete_knowledge_base


class FakeStorage:
    removed: list[str] = []

    def __init__(self) -> None:
        pass

    def remove_object(self, object_name: str) -> None:
        self.removed.append(object_name)


async def _create_user(async_session, username: str, role_name: RoleName) -> User:
    org = Organization(name=f"{username} Org")
    role = await async_session.scalar(select(Role).where(Role.name == role_name))
    if role is None:
        role = Role(name=role_name, description=role_name.value)
        async_session.add(role)
    user = User(
        username=username,
        email=f"{username}@example.com",
        password_hash=hash_password("ChangeMe123!"),
        org_id=None,
    )
    async_session.add_all([org, user])
    await async_session.flush()
    user.org_id = org.id
    async_session.add(UserRole(user_id=user.id, role_id=role.id))
    await async_session.flush()
    loaded = await async_session.scalar(
        select(User).options(selectinload(User.roles)).where(User.id == user.id)
    )
    assert loaded is not None
    return loaded


async def _create_kb_with_document(
    async_session, owner: User
) -> tuple[KnowledgeBase, Document]:
    kb = KnowledgeBase(
        name=f"KB {uuid.uuid4().hex[:8]}",
        visibility_scope=VisibilityScope.company,
        org_id=owner.org_id,
        owner_id=owner.id,
        chunk_method=ChunkMethod.sentence,
        chunk_size=1024,
        chunk_overlap=128,
    )
    async_session.add(kb)
    await async_session.flush()

    doc = Document(
        kb_id=kb.id,
        file_name="example.txt",
        file_uri="minio://rag/example.txt",
        file_type="text/plain",
        size=120,
        status=DocumentStatus.ready,
        created_by=owner.id,
    )
    async_session.add(doc)
    await async_session.flush()

    async_session.add(
        DocumentBlock(
            document_id=doc.id,
            block_type=BlockType.text,
            content="Hello",
            block_order=1,
        )
    )
    async_session.add(
        Chunk(
            kb_id=kb.id,
            document_id=doc.id,
            content="Hello",
            content_hash=uuid.uuid4().hex,
            visibility_scope=VisibilityScope.company,
            org_id=owner.org_id,
            owner_id=owner.id,
        )
    )
    async_session.add(
        KnowledgeBaseAcl(
            kb_id=kb.id,
            subject_type=SubjectType.user,
            subject_id=owner.id,
            can_read=True,
        )
    )
    await async_session.commit()
    return kb, doc


@pytest.mark.asyncio
async def test_delete_document_removes_content_and_object(async_session, monkeypatch):
    FakeStorage.removed = []
    monkeypatch.setattr("app.services.document_service.MinioStorage", FakeStorage)

    owner = await _create_user(async_session, "delete_doc_owner", RoleName.user)
    _kb, doc = await _create_kb_with_document(async_session, owner)

    await delete_document(async_session, doc.id, owner)

    assert (
        await async_session.scalar(select(Document).where(Document.id == doc.id))
        is None
    )
    assert (
        await async_session.scalar(
            select(DocumentBlock).where(DocumentBlock.document_id == doc.id)
        )
        is None
    )
    assert (
        await async_session.scalar(select(Chunk).where(Chunk.document_id == doc.id))
        is None
    )
    assert FakeStorage.removed == ["example.txt"]


@pytest.mark.asyncio
async def test_delete_knowledge_base_removes_related_records(
    async_session, monkeypatch
):
    FakeStorage.removed = []
    monkeypatch.setattr("app.services.knowledge_base_service.MinioStorage", FakeStorage)

    owner = await _create_user(async_session, "delete_kb_owner", RoleName.user)
    kb, doc = await _create_kb_with_document(async_session, owner)

    await delete_knowledge_base(async_session, kb.id, owner)

    assert (
        await async_session.scalar(
            select(KnowledgeBase).where(KnowledgeBase.id == kb.id)
        )
        is None
    )
    assert (
        await async_session.scalar(select(Document).where(Document.id == doc.id))
        is None
    )
    assert await async_session.scalar(select(Chunk).where(Chunk.kb_id == kb.id)) is None
    assert (
        await async_session.scalar(
            select(DocumentBlock).where(DocumentBlock.document_id == doc.id)
        )
        is None
    )
    assert (
        await async_session.scalar(
            select(KnowledgeBaseAcl).where(KnowledgeBaseAcl.kb_id == kb.id)
        )
        is None
    )
    assert FakeStorage.removed == ["example.txt"]


@pytest.mark.asyncio
async def test_non_owner_cannot_delete_knowledge_base(async_session, monkeypatch):
    FakeStorage.removed = []
    monkeypatch.setattr("app.services.knowledge_base_service.MinioStorage", FakeStorage)

    owner = await _create_user(async_session, "delete_forbidden_owner", RoleName.user)
    other = await _create_user(async_session, "delete_forbidden_other", RoleName.user)
    kb, _doc = await _create_kb_with_document(async_session, owner)

    with pytest.raises(AppError) as exc_info:
        await delete_knowledge_base(async_session, kb.id, other)

    assert exc_info.value.status_code == 403
    assert (
        await async_session.scalar(
            select(KnowledgeBase).where(KnowledgeBase.id == kb.id)
        )
        is not None
    )
    assert FakeStorage.removed == []
