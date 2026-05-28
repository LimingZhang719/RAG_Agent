from __future__ import annotations

from uuid import UUID

from sqlalchemy import delete, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppError
from app.db.models.enums import RoleName, VisibilityScope
from app.db.models.knowledge_base import KnowledgeBase
from app.db.models.user import User
from app.schemas.knowledge_base import KnowledgeBaseCreate, KnowledgeBaseUpdate


def _is_admin(user: User) -> bool:
    return any(role.name == RoleName.admin for role in user.roles)


def _visibility_filters(user: User):
    return or_(
        KnowledgeBase.visibility_scope == VisibilityScope.company,
        (
            (KnowledgeBase.visibility_scope == VisibilityScope.department)
            & (KnowledgeBase.org_id == user.org_id)
        ),
        (
            (KnowledgeBase.visibility_scope == VisibilityScope.personal)
            & (KnowledgeBase.owner_id == user.id)
        ),
    )


async def list_knowledge_bases(session: AsyncSession, user: User) -> list[KnowledgeBase]:
    query = select(KnowledgeBase)
    if not _is_admin(user):
        query = query.where(_visibility_filters(user))
    result = await session.execute(query.order_by(KnowledgeBase.created_at.desc()))
    return list(result.scalars().all())


async def get_knowledge_base(
    session: AsyncSession, kb_id: UUID, user: User
) -> KnowledgeBase:
    result = await session.execute(
        select(KnowledgeBase).where(KnowledgeBase.id == kb_id)
    )
    kb = result.scalar_one_or_none()
    if kb is None:
        raise AppError("Knowledge base not found", status_code=404)
    if not _is_admin(user) and not _can_access_kb(kb, user):
        raise AppError("Forbidden", status_code=403)
    return kb


def _can_access_kb(kb: KnowledgeBase, user: User) -> bool:
    if kb.visibility_scope == VisibilityScope.company:
        return True
    if kb.visibility_scope == VisibilityScope.department:
        return kb.org_id == user.org_id
    if kb.visibility_scope == VisibilityScope.personal:
        return kb.owner_id == user.id
    return False


async def create_knowledge_base(
    session: AsyncSession, user: User, payload: KnowledgeBaseCreate
) -> KnowledgeBase:
    org_id = payload.org_id
    owner_id = user.id

    if payload.visibility_scope == VisibilityScope.department:
        if org_id is None:
            org_id = user.org_id
        if org_id is None:
            raise AppError("Organization required", status_code=400)

    if payload.visibility_scope == VisibilityScope.company and not _is_admin(user):
        raise AppError("Only admin can create company knowledge base", status_code=403)

    kb = KnowledgeBase(
        name=payload.name,
        description=payload.description,
        visibility_scope=payload.visibility_scope,
        org_id=org_id,
        owner_id=owner_id,
        is_active=True,
    )
    session.add(kb)
    await session.commit()
    await session.refresh(kb)
    return kb


async def update_knowledge_base(
    session: AsyncSession,
    kb_id: UUID,
    user: User,
    payload: KnowledgeBaseUpdate,
) -> KnowledgeBase:
    kb = await get_knowledge_base(session, kb_id, user)
    if not _is_admin(user) and kb.owner_id != user.id:
        raise AppError("Forbidden", status_code=403)

    data = payload.model_dump(exclude_unset=True)
    for field, value in data.items():
        setattr(kb, field, value)
    await session.commit()
    await session.refresh(kb)
    return kb


async def delete_knowledge_base(
    session: AsyncSession, kb_id: UUID, user: User
) -> None:
    kb = await get_knowledge_base(session, kb_id, user)
    if not _is_admin(user) and kb.owner_id != user.id:
        raise AppError("Forbidden", status_code=403)
    await session.execute(delete(KnowledgeBase).where(KnowledgeBase.id == kb.id))
    await session.commit()
