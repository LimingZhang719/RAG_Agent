from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.organization import Organization
from app.db.session import get_session
from app.schemas.organization import OrganizationResponse

router = APIRouter(prefix="/organizations", tags=["organizations"])
SessionDep = Annotated[AsyncSession, Depends(get_session)]


@router.get("", response_model=list[OrganizationResponse])
async def list_organizations(
    session: SessionDep,
) -> list[OrganizationResponse]:
    result = await session.execute(select(Organization).order_by(Organization.name))
    organizations = result.scalars().all()
    return [
        OrganizationResponse(
            id=organization.id,
            name=organization.name,
            parent_id=organization.parent_id,
            path=organization.path,
        )
        for organization in organizations
    ]
