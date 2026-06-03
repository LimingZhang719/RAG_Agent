from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import AppError
from app.db.models.enums import RoleName, SettingValueType
from app.db.models.settings import SystemSetting
from app.db.models.user import User
from app.schemas.settings import SystemSettingUpsert


def has_role(user: User, role: RoleName) -> bool:
    return any(item.name == role for item in user.roles)


def require_admin(user: User) -> None:
    if not has_role(user, RoleName.admin):
        raise AppError("Forbidden", status_code=403)


def require_finance(user: User) -> None:
    if not (has_role(user, RoleName.admin) or has_role(user, RoleName.finance)):
        raise AppError("Forbidden", status_code=403)


def _wrap_setting_value(value: Any, value_type: SettingValueType) -> dict[str, Any]:
    return {"raw": value, "type": value_type.value}


def unwrap_setting_value(item: SystemSetting | None, default: Any = None) -> Any:
    if item is None or item.value is None:
        return default
    if isinstance(item.value, dict) and "raw" in item.value:
        return item.value["raw"]
    return item.value


async def get_setting(
    session: AsyncSession,
    key: str,
    default: Any = None,
) -> Any:
    result = await session.execute(select(SystemSetting).where(SystemSetting.key == key))
    return unwrap_setting_value(result.scalar_one_or_none(), default)


async def get_invoice_title(session: AsyncSession) -> str:
    configured = await get_setting(session, "expense.invoice_title", None)
    return configured or getattr(settings, "expense_invoice_title", "默认公司")


async def get_reimbursement_days(session: AsyncSession) -> int:
    configured = await get_setting(session, "expense.reimbursement_days", None)
    try:
        return int(configured)
    except (TypeError, ValueError):
        return 180


async def list_settings(session: AsyncSession) -> list[SystemSetting]:
    result = await session.execute(select(SystemSetting).order_by(SystemSetting.key.asc()))
    return list(result.scalars().all())


async def upsert_setting(
    session: AsyncSession,
    payload: SystemSettingUpsert,
    user: User,
) -> SystemSetting:
    require_admin(user)
    result = await session.execute(select(SystemSetting).where(SystemSetting.key == payload.key))
    item = result.scalar_one_or_none()
    if item is None:
        item = SystemSetting(key=payload.key, value_type=payload.value_type, group_name=payload.group_name)
        session.add(item)
    if item.is_secret and payload.value in (None, "", {"raw": ""}):
        pass
    else:
        item.value = _wrap_setting_value(payload.value, payload.value_type)
    item.value_type = payload.value_type
    item.group_name = payload.group_name
    item.description = payload.description
    item.is_secret = payload.is_secret
    item.is_runtime_editable = payload.is_runtime_editable
    item.updated_by = user.id
    await session.commit()
    await session.refresh(item)
    return item


def mask_secret(item: SystemSetting) -> SystemSetting:
    if item.is_secret:
        item.value = {"configured": bool(item.value)}
    return item
