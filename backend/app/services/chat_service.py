from __future__ import annotations

from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import ValidationError

from app.core.exceptions import AppError
from app.db.models.chat import ChatMessage, ChatSession
from app.db.models.enums import MessageRole
from app.db.models.retrieval import RetrievalLog
from app.db.models.user import User
from app.schemas.chat import ChatSessionSettings, ChatSessionUpdate


def _ensure_session_owner(session_obj: ChatSession, user: User) -> None:
    if session_obj.user_id != user.id:
        raise AppError("Forbidden", status_code=403)


def build_session_title(question: str) -> str:
    title = " ".join(question.split())
    return title[:255] or "未命名会话"


async def create_session(
    session: AsyncSession,
    user: User,
    title: str | None,
    kb_ids: list[UUID],
    settings: ChatSessionSettings | None = None,
) -> ChatSession:
    chat_session = ChatSession(
        user_id=user.id,
        title=title,
        kb_ids=[str(kb_id) for kb_id in kb_ids],
        metadata_=_build_metadata_with_settings(None, settings),
    )
    session.add(chat_session)
    await session.commit()
    await session.refresh(chat_session)
    return attach_session_settings(chat_session)


def get_session_settings(chat_session: ChatSession) -> ChatSessionSettings:
    metadata = chat_session.metadata_ or {}
    raw_settings = metadata.get("settings") if isinstance(metadata, dict) else None
    if not isinstance(raw_settings, dict):
        return ChatSessionSettings()
    try:
        return ChatSessionSettings.model_validate(raw_settings)
    except ValidationError:
        return ChatSessionSettings()


def attach_session_settings(chat_session: ChatSession) -> ChatSession:
    setattr(chat_session, "settings", get_session_settings(chat_session))
    return chat_session


def _build_metadata_with_settings(
    metadata: dict | None, settings_payload: ChatSessionSettings | None
) -> dict | None:
    if settings_payload is None:
        return metadata
    next_metadata = dict(metadata or {})
    next_metadata["settings"] = settings_payload.model_dump()
    return next_metadata


async def update_session(
    session: AsyncSession,
    session_id: UUID,
    user: User,
    payload: ChatSessionUpdate,
) -> ChatSession:
    chat_session = await get_session(session, session_id, user)
    if payload.title is not None:
        chat_session.title = payload.title
    if payload.kb_ids is not None:
        chat_session.kb_ids = [str(kb_id) for kb_id in payload.kb_ids]
    if payload.settings is not None:
        chat_session.metadata_ = _build_metadata_with_settings(
            chat_session.metadata_, payload.settings
        )
    await session.commit()
    await session.refresh(chat_session)
    return attach_session_settings(chat_session)


async def delete_session(session: AsyncSession, session_id: UUID, user: User) -> None:
    chat_session = await get_session(session, session_id, user)
    await session.execute(
        delete(RetrievalLog).where(RetrievalLog.session_id == chat_session.id)
    )
    await session.delete(chat_session)
    await session.commit()


async def ensure_session_title(
    session: AsyncSession, chat_session: ChatSession, fallback_question: str
) -> None:
    if chat_session.title:
        return

    result = await session.execute(
        select(ChatMessage.content)
        .where(
            ChatMessage.session_id == chat_session.id,
            ChatMessage.role == MessageRole.user,
        )
        .order_by(ChatMessage.created_at.asc())
        .limit(1)
    )
    first_question = result.scalar_one_or_none() or fallback_question
    chat_session.title = build_session_title(first_question)
    await session.commit()
    await session.refresh(chat_session)


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
    return attach_session_settings(chat_session)


async def list_sessions(session: AsyncSession, user: User) -> list[ChatSession]:
    result = await session.execute(
        select(ChatSession)
        .where(ChatSession.user_id == user.id)
        .order_by(ChatSession.created_at.desc())
    )
    return [attach_session_settings(item) for item in result.scalars().all()]


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
