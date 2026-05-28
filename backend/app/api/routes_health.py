from fastapi import APIRouter
from sqlalchemy import text

from app.core.config import settings
from app.db.session import engine

router = APIRouter()


@router.get("/health")
async def health() -> dict[str, str]:
    return {
        "status": "ok",
        "service": settings.app_name,
        "version": settings.app_version,
    }


@router.get("/health/db")
async def database_health() -> dict[str, str]:
    async with engine.connect() as connection:
        await connection.execute(text("SELECT 1"))
    return {"status": "ok", "database": "reachable"}
