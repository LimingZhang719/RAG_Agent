from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import AppError
from app.core.security import hash_password, verify_password
from app.db.models.enums import ApprovalStatus, RoleName
from app.db.models.organization import Organization
from app.db.models.role import Role
from app.db.models.user import User
from app.db.models.user_role import UserRole
from app.schemas.auth import RegisterRequest

APPROVAL_REQUIRED_ROLES = {RoleName.department_admin, RoleName.user}


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


async def register_user(session: AsyncSession, payload: RegisterRequest) -> User:
    username = payload.username.strip()
    email = payload.email.strip() if payload.email else None
    full_name = payload.full_name.strip() if payload.full_name else None
    if not username:
        raise AppError("Username is required", code="INVALID_USERNAME", status_code=400)

    duplicate_filter = User.username == username
    if email:
        duplicate_filter = or_(duplicate_filter, User.email == email)

    existing_user = await session.scalar(select(User).where(duplicate_filter))
    if existing_user is not None:
        raise AppError(
            "Username or email already exists",
            code="USER_ALREADY_EXISTS",
            status_code=409,
        )

    organization = await session.scalar(
        select(Organization).where(Organization.id == payload.org_id)
    )
    if organization is None:
        raise AppError(
            "Organization not found", code="ORGANIZATION_NOT_FOUND", status_code=404
        )

    role = await session.scalar(select(Role).where(Role.name == payload.role))
    if role is None:
        raise AppError("Role not found", code="ROLE_NOT_FOUND", status_code=400)

    needs_approval = payload.role in APPROVAL_REQUIRED_ROLES
    user = User(
        username=username,
        email=email,
        full_name=full_name,
        password_hash=hash_password(payload.password),
        org_id=organization.id,
        is_active=not needs_approval,
        approval_status=(
            ApprovalStatus.pending if needs_approval else ApprovalStatus.approved
        ),
    )
    session.add(user)
    await session.flush()
    session.add(UserRole(user_id=user.id, role_id=role.id))
    await session.commit()

    result = await session.execute(
        select(User).options(selectinload(User.roles)).where(User.id == user.id)
    )
    return result.scalar_one()


def _role_names(user: User) -> set[RoleName]:
    return {role.name for role in user.roles}


def _ensure_can_review(reviewer: User, target: User) -> None:
    reviewer_roles = _role_names(reviewer)
    target_roles = _role_names(target)

    if RoleName.admin in reviewer_roles and RoleName.department_admin in target_roles:
        return

    if (
        RoleName.department_admin in reviewer_roles
        and RoleName.user in target_roles
        and reviewer.org_id == target.org_id
    ):
        return

    raise AppError("No approval permission", code="FORBIDDEN", status_code=403)


async def list_pending_approvals(session: AsyncSession, reviewer: User) -> list[User]:
    reviewer_roles = _role_names(reviewer)
    query = (
        select(User)
        .options(selectinload(User.roles), selectinload(User.organization))
        .where(User.approval_status == ApprovalStatus.pending)
        .order_by(User.created_at.desc())
    )

    if RoleName.admin in reviewer_roles:
        query = query.where(User.roles.any(Role.name == RoleName.department_admin))
    elif RoleName.department_admin in reviewer_roles:
        query = query.where(
            User.roles.any(Role.name == RoleName.user),
            User.org_id == reviewer.org_id,
        )
    else:
        raise AppError("No approval permission", code="FORBIDDEN", status_code=403)

    result = await session.execute(query)
    return list(result.scalars().unique().all())


async def update_registration_approval(
    session: AsyncSession,
    reviewer: User,
    user_id: UUID,
    approved: bool,
) -> User:
    result = await session.execute(
        select(User)
        .options(selectinload(User.roles), selectinload(User.organization))
        .where(User.id == user_id)
    )
    target = result.scalar_one_or_none()
    if target is None:
        raise AppError("User not found", code="USER_NOT_FOUND", status_code=404)
    if target.approval_status != ApprovalStatus.pending:
        raise AppError(
            "Registration is not pending approval",
            code="APPROVAL_NOT_PENDING",
            status_code=400,
        )

    _ensure_can_review(reviewer, target)

    target.approval_status = (
        ApprovalStatus.approved if approved else ApprovalStatus.rejected
    )
    target.is_active = approved
    target.approved_by = reviewer.id
    target.approved_at = datetime.now(UTC)
    await session.commit()
    return target
