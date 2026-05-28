from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user
from app.db.session import get_session
from app.schemas.knowledge_base import (
    KnowledgeBaseCreate,
    KnowledgeBaseResponse,
    KnowledgeBaseUpdate,
)
from app.services.knowledge_base_service import (
    create_knowledge_base,
    delete_knowledge_base,
    get_knowledge_base,
    list_knowledge_bases,
    update_knowledge_base,
)

router = APIRouter(prefix="/knowledge-bases", tags=["knowledge-bases"])


@router.get("", response_model=list[KnowledgeBaseResponse])
async def list_kbs(
    session: AsyncSession = Depends(get_session),
    current_user=Depends(get_current_user),
) -> list[KnowledgeBaseResponse]:
    kbs = await list_knowledge_bases(session, current_user)
    return [KnowledgeBaseResponse.model_validate(kb) for kb in kbs]


@router.post("", response_model=KnowledgeBaseResponse)
async def create_kb(
    payload: KnowledgeBaseCreate,
    session: AsyncSession = Depends(get_session),
    current_user=Depends(get_current_user),
) -> KnowledgeBaseResponse:
    kb = await create_knowledge_base(session, current_user, payload)
    return KnowledgeBaseResponse.model_validate(kb)


@router.get("/{kb_id}", response_model=KnowledgeBaseResponse)
async def get_kb(
    kb_id: UUID,
    session: AsyncSession = Depends(get_session),
    current_user=Depends(get_current_user),
) -> KnowledgeBaseResponse:
    kb = await get_knowledge_base(session, kb_id, current_user)
    return KnowledgeBaseResponse.model_validate(kb)


@router.patch("/{kb_id}", response_model=KnowledgeBaseResponse)
async def update_kb(
    kb_id: UUID,
    payload: KnowledgeBaseUpdate,
    session: AsyncSession = Depends(get_session),
    current_user=Depends(get_current_user),
) -> KnowledgeBaseResponse:
    kb = await update_knowledge_base(session, kb_id, current_user, payload)
    return KnowledgeBaseResponse.model_validate(kb)


@router.delete("/{kb_id}")
async def delete_kb(
    kb_id: UUID,
    session: AsyncSession = Depends(get_session),
    current_user=Depends(get_current_user),
) -> dict[str, str]:
    await delete_knowledge_base(session, kb_id, current_user)
    return {"status": "ok"}
