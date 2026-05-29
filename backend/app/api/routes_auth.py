from __future__ import annotations

from datetime import UTC, datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppError
from app.core.security import create_access_token, get_current_user, get_token_expiry
from app.db.models.enums import ApprovalStatus
from app.db.models.user import User
from app.db.session import get_session
from app.schemas.auth import (
    ApprovalUserResponse,
    LoginRequest,
    PendingApprovalResponse,
    RegisterRequest,
    TokenResponse,
    UserResponse,
)
from app.services.auth_service import (
    authenticate_user,
    list_pending_approvals,
    register_user,
    update_registration_approval,
)

router = APIRouter(prefix="/auth", tags=["auth"])
SessionDep = Annotated[AsyncSession, Depends(get_session)]
CurrentUserDep = Annotated[User, Depends(get_current_user)]


def _to_approval_response(user: User) -> ApprovalUserResponse:
    return ApprovalUserResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        org_id=user.org_id,
        org_name=user.organization.name if user.organization else None,
        roles=[role.name.value for role in user.roles],
        approval_status=user.approval_status.value,
        created_at=user.created_at,
    )


@router.post("/login", response_model=TokenResponse)
async def login(payload: LoginRequest, session: SessionDep) -> TokenResponse:
    user = await authenticate_user(session, payload.username, payload.password)
    if user is None:
        raise AppError(
            "Invalid credentials", code="INVALID_CREDENTIALS", status_code=401
        )
    if user.approval_status == ApprovalStatus.pending:
        raise AppError(
            "User pending approval", code="PENDING_APPROVAL", status_code=403
        )
    if not user.is_active:
        raise AppError("User inactive", code="USER_INACTIVE", status_code=403)
    user.last_login_at = datetime.now(UTC)
    await session.commit()
    token = create_access_token(str(user.id))
    expires_at = get_token_expiry()
    return TokenResponse(access_token=token, token_type="bearer", expires_at=expires_at)


@router.post("/register", response_model=TokenResponse | PendingApprovalResponse)
async def register(
    payload: RegisterRequest, session: SessionDep
) -> TokenResponse | PendingApprovalResponse:
    user = await register_user(session, payload)
    if user.approval_status == ApprovalStatus.pending:
        return PendingApprovalResponse()

    user.last_login_at = datetime.now(UTC)
    await session.commit()
    token = create_access_token(str(user.id))
    expires_at = get_token_expiry()
    return TokenResponse(access_token=token, token_type="bearer", expires_at=expires_at)


@router.get("/me", response_model=UserResponse)
async def me(current_user: CurrentUserDep) -> UserResponse:
    return UserResponse(
        id=current_user.id,
        username=current_user.username,
        email=current_user.email,
        full_name=current_user.full_name,
        org_id=current_user.org_id,
        roles=[role.name.value for role in current_user.roles],
        is_active=current_user.is_active,
        approval_status=current_user.approval_status.value,
        last_login_at=current_user.last_login_at,
    )


@router.get("/approvals", response_model=list[ApprovalUserResponse])
async def list_approvals(
    session: SessionDep, current_user: CurrentUserDep
) -> list[ApprovalUserResponse]:
    users = await list_pending_approvals(session, current_user)
    return [_to_approval_response(user) for user in users]


@router.post("/approvals/{user_id}/approve", response_model=ApprovalUserResponse)
async def approve_registration(
    user_id: UUID, session: SessionDep, current_user: CurrentUserDep
) -> ApprovalUserResponse:
    user = await update_registration_approval(
        session, current_user, user_id, approved=True
    )
    return _to_approval_response(user)


@router.post("/approvals/{user_id}/reject", response_model=ApprovalUserResponse)
async def reject_registration(
    user_id: UUID, session: SessionDep, current_user: CurrentUserDep
) -> ApprovalUserResponse:
    user = await update_registration_approval(
        session, current_user, user_id, approved=False
    )
    return _to_approval_response(user)
