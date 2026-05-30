from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user
from app.db.session import get_session
from app.schemas.chat import (
    ChatMessageListResponse,
    ChatMessageResponse,
    ChatSessionCreate,
    ChatSessionResponse,
    ChatSessionUpdate,
    ChatStreamRequest,
)
from app.services.chat_service import (
    delete_session,
    get_session as get_chat_session,
    list_messages,
    list_sessions,
    update_session,
)
from app.services.rag_service import stream_chat

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/sessions", response_model=ChatSessionResponse)
async def create_chat_session(
    payload: ChatSessionCreate,
    session: AsyncSession = Depends(get_session),
    current_user=Depends(get_current_user),
) -> ChatSessionResponse:
    from app.services.chat_service import create_session

    chat_session = await create_session(
        session=session,
        user=current_user,
        title=payload.title,
        kb_ids=payload.kb_ids,
        settings=payload.settings,
    )
    return ChatSessionResponse.model_validate(chat_session)


@router.get("/sessions", response_model=list[ChatSessionResponse])
async def list_chat_sessions(
    session: AsyncSession = Depends(get_session),
    current_user=Depends(get_current_user),
) -> list[ChatSessionResponse]:
    sessions = await list_sessions(session, current_user)
    return [ChatSessionResponse.model_validate(item) for item in sessions]


@router.get("/sessions/{session_id}", response_model=ChatSessionResponse)
async def get_chat_session_detail(
    session_id: UUID,
    session: AsyncSession = Depends(get_session),
    current_user=Depends(get_current_user),
) -> ChatSessionResponse:
    chat_session = await get_chat_session(session, session_id, current_user)
    return ChatSessionResponse.model_validate(chat_session)


@router.patch("/sessions/{session_id}", response_model=ChatSessionResponse)
async def update_chat_session(
    session_id: UUID,
    payload: ChatSessionUpdate,
    session: AsyncSession = Depends(get_session),
    current_user=Depends(get_current_user),
) -> ChatSessionResponse:
    chat_session = await update_session(session, session_id, current_user, payload)
    return ChatSessionResponse.model_validate(chat_session)


@router.delete("/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_chat_session(
    session_id: UUID,
    session: AsyncSession = Depends(get_session),
    current_user=Depends(get_current_user),
) -> Response:
    await delete_session(session, session_id, current_user)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/messages", response_model=ChatMessageListResponse)
async def list_chat_messages(
    session_id: UUID,
    session: AsyncSession = Depends(get_session),
    current_user=Depends(get_current_user),
) -> ChatMessageListResponse:
    messages = await list_messages(session, session_id, current_user)
    return ChatMessageListResponse(
        items=[ChatMessageResponse.model_validate(item) for item in messages]
    )


@router.post("/stream")
async def chat_stream(
    payload: ChatStreamRequest,
    session: AsyncSession = Depends(get_session),
    current_user=Depends(get_current_user),
):
    return await stream_chat(
        session=session,
        user=current_user,
        question=payload.question,
        kb_ids=payload.kb_ids,
        session_id=payload.session_id,
        top_k=payload.top_k,
        rerank_enabled=payload.rerank_enabled,
        temperature=payload.temperature,
        system_prompt=payload.system_prompt,
    )
