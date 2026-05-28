from __future__ import annotations

from datetime import timedelta

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppError
from app.core.security import create_access_token, get_current_user, get_token_expiry
from app.db.session import get_session
from app.schemas.auth import LoginRequest, TokenResponse, UserResponse
from app.services.auth_service import authenticate_user

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
async def login(
    payload: LoginRequest, session: AsyncSession = Depends(get_session)
) -> TokenResponse:
    user = await authenticate_user(session, payload.username, payload.password)
    if user is None:
        raise AppError("Invalid credentials", code="INVALID_CREDENTIALS", status_code=401)
    token = create_access_token(str(user.id))
    expires_at = get_token_expiry()
    return TokenResponse(access_token=token, token_type="bearer", expires_at=expires_at)


@router.get("/me", response_model=UserResponse)
async def me(current_user=Depends(get_current_user)) -> UserResponse:
    return UserResponse(
        id=current_user.id,
        username=current_user.username,
        email=current_user.email,
        full_name=current_user.full_name,
        org_id=current_user.org_id,
        roles=[role.name.value for role in current_user.roles],
        is_active=current_user.is_active,
        last_login_at=current_user.last_login_at,
    )
