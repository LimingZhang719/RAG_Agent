from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.security import verify_password
from app.db.models.user import User


async def get_user_by_username(
    session: AsyncSession, username: str
) -> User | None:
    result = await session.execute(
        select(User)
        .options(selectinload(User.roles))
        .where(User.username == username)
    )
    return result.scalar_one_or_none()


async def get_user_by_id(session: AsyncSession, user_id: UUID) -> User | None:
    result = await session.execute(
        select(User).options(selectinload(User.roles)).where(User.id == user_id)
    )
    return result.scalar_one_or_none()


async def authenticate_user(
    session: AsyncSession, username: str, password: str
) -> User | None:
    user = await get_user_by_username(session, username)
    if user is None:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user
