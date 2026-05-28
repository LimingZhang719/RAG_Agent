from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppError
from app.db.models.chat import ChatMessage, ChatSession
from app.db.models.enums import MessageRole
from app.db.models.user import User


def _ensure_session_owner(session_obj: ChatSession, user: User) -> None:
    if session_obj.user_id != user.id:
        raise AppError("Forbidden", status_code=403)


async def create_session(
    session: AsyncSession, user: User, title: str | None, kb_ids: list[UUID]
) -> ChatSession:
    chat_session = ChatSession(
        user_id=user.id,
        title=title,
        kb_ids=[str(kb_id) for kb_id in kb_ids],
    )
    session.add(chat_session)
    await session.commit()
    await session.refresh(chat_session)
    return chat_session


async def get_session(
    session: AsyncSession, session_id: UUID, user: User
) -> ChatSession:
    result = await session.execute(
        select(ChatSession).where(ChatSession.id == session_id)
    )
    chat_session = result.scalar_one_or_none()
    if chat_session is None:
        raise AppError("Chat session not found", status_code=404)
    _ensure_session_owner(chat_session, user)
    return chat_session


async def list_sessions(session: AsyncSession, user: User) -> list[ChatSession]:
    result = await session.execute(
        select(ChatSession)
        .where(ChatSession.user_id == user.id)
        .order_by(ChatSession.created_at.desc())
    )
    return list(result.scalars().all())


async def list_messages(
    session: AsyncSession, session_id: UUID, user: User
) -> list[ChatMessage]:
    chat_session = await get_session(session, session_id, user)
    result = await session.execute(
        select(ChatMessage)
        .where(ChatMessage.session_id == chat_session.id)
        .order_by(ChatMessage.created_at.asc())
    )
    return list(result.scalars().all())


async def create_message(
    session: AsyncSession,
    session_id: UUID,
    role: MessageRole,
    content: str,
    citations: list[dict] | None,
    created_by: UUID | None,
) -> ChatMessage:
    message = ChatMessage(
        session_id=session_id,
        role=role,
        content=content,
        citations=citations,
        created_by=created_by,
    )
    session.add(message)
    await session.commit()
    await session.refresh(message)
    return message
