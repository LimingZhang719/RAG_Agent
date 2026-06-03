from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user
from app.db.session import get_session
from app.schemas.settings import SystemSettingResponse, SystemSettingUpsert
from app.services.settings_service import list_settings, require_admin, upsert_setting

router = APIRouter(prefix="/settings", tags=["settings"])


@router.get("", response_model=list[SystemSettingResponse])
async def get_settings_list(
    session: AsyncSession = Depends(get_session),
    current_user=Depends(get_current_user),
) -> list[SystemSettingResponse]:
    require_admin(current_user)
    items = await list_settings(session)
    responses: list[SystemSettingResponse] = []
    for item in items:
        data = SystemSettingResponse.model_validate(item)
        if item.is_secret:
            data.value = {"configured": bool(item.value)}
        elif isinstance(item.value, dict) and "raw" in item.value:
            data.value = item.value["raw"]
        responses.append(data)
    return responses


@router.put("", response_model=SystemSettingResponse)
async def put_setting(
    payload: SystemSettingUpsert,
    session: AsyncSession = Depends(get_session),
    current_user=Depends(get_current_user),
) -> SystemSettingResponse:
    item = await upsert_setting(session, payload, current_user)
    response = SystemSettingResponse.model_validate(item)
    if item.is_secret:
        response.value = {"configured": bool(item.value)}
    elif isinstance(item.value, dict) and "raw" in item.value:
        response.value = item.value["raw"]
    return response
