from __future__ import annotations

import uuid

import pytest
from sqlalchemy import select

from app.core.security import hash_password
from app.db.models.chat import ChatMessage, ChatSession
from app.db.models.document import Chunk, Document
from app.db.models.enums import (
    ChunkMethod,
    DocumentStatus,
    ExpenseStatus,
    MessageRole,
    RoleName,
    VisibilityScope,
)
from app.db.models.expense import ExpenseClaim
from app.db.models.knowledge_base import KnowledgeBase
from app.db.models.organization import Organization
from app.db.models.role import Role
from app.db.models.user import User
from app.db.models.user_role import UserRole


@pytest.mark.asyncio
async def test_user_role_kb_flow(async_session):
    org = Organization(name="Test Org")
    async_session.add(org)
    await async_session.flush()

    role = Role(name=RoleName.user, description="user")
    async_session.add(role)
    await async_session.flush()

    user = User(
        username="tester",
        email="tester@example.com",
        password_hash=hash_password("ChangeMe123!"),
        org_id=org.id,
    )
    async_session.add(user)
    await async_session.flush()

    async_session.add(UserRole(user_id=user.id, role_id=role.id))

    kb = KnowledgeBase(
        name="Company KB",
        description="Test KB",
        visibility_scope=VisibilityScope.company,
        org_id=org.id,
        owner_id=user.id,
        chunk_method=ChunkMethod.sentence,
        chunk_size=1024,
        chunk_overlap=128,
    )
    async_session.add(kb)
    await async_session.commit()

    result = await async_session.execute(
        select(KnowledgeBase).where(KnowledgeBase.id == kb.id)
    )
    loaded = result.scalar_one()
    assert loaded.name == "Company KB"


@pytest.mark.asyncio
async def test_document_chat_and_expense(async_session):
    org = Organization(name="Doc Org")
    async_session.add(org)
    await async_session.flush()

    user = User(
        username="doc_user",
        email="doc_user@example.com",
        password_hash=hash_password("ChangeMe123!"),
        org_id=org.id,
    )
    async_session.add(user)
    await async_session.flush()

    kb = KnowledgeBase(
        name="Docs",
        visibility_scope=VisibilityScope.company,
        org_id=org.id,
        owner_id=user.id,
        chunk_method=ChunkMethod.sentence,
        chunk_size=1024,
        chunk_overlap=128,
    )
    async_session.add(kb)
    await async_session.flush()

    doc = Document(
        kb_id=kb.id,
        file_name="example.txt",
        file_uri="minio://bucket/example.txt",
        file_type="text/plain",
        size=120,
        status=DocumentStatus.pending,
        created_by=user.id,
    )
    async_session.add(doc)
    await async_session.flush()

    chunk = Chunk(
        kb_id=kb.id,
        document_id=doc.id,
        content="Hello",
        content_hash=uuid.uuid4().hex,
        visibility_scope=VisibilityScope.company,
        org_id=org.id,
        owner_id=user.id,
    )
    async_session.add(chunk)

    session = ChatSession(user_id=user.id, title="Test")
    async_session.add(session)
    await async_session.flush()

    message = ChatMessage(
        session_id=session.id,
        role=MessageRole.user,
        content="Hi",
        created_by=user.id,
    )
    async_session.add(message)

    claim = ExpenseClaim(user_id=user.id, status=ExpenseStatus.draft)
    async_session.add(claim)

    await async_session.commit()

    loaded = await async_session.scalar(
        select(ChatMessage).where(ChatMessage.id == message.id)
    )
    assert loaded is not None
