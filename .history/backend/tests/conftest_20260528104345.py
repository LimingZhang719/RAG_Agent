from __future__ import annotations

import os

import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings
from app.db.base import Base

TEST_SCHEMA = "test_schema"


@pytest_asyncio.fixture(scope="session")
async def async_engine():
    database_url = os.getenv("TEST_DATABASE_URL", settings.database_url)
    engine = create_async_engine(
        database_url,
        execution_options={"schema_translate_map": {None: TEST_SCHEMA}},
    )

    async with engine.begin() as conn:
        result = await conn.execute(
            text("SELECT 1 FROM pg_extension WHERE extname = 'vector'")
        )
        if result.first() is None:
            try:
                await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
            except Exception as exc:
                pytest.skip(f"pgvector extension not available: {exc}")

        result = await conn.execute(
            text("SELECT 1 FROM pg_extension WHERE extname = 'vector'")
        )
        if result.first() is None:
            pytest.skip("pgvector extension not installed")
        await conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {TEST_SCHEMA}"))
        await conn.execute(text(f"SET search_path TO {TEST_SCHEMA}"))
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    async with engine.begin() as conn:
        await conn.execute(text(f"DROP SCHEMA IF EXISTS {TEST_SCHEMA} CASCADE"))
    await engine.dispose()


@pytest_asyncio.fixture()
async def async_session(async_engine):
    session_maker = async_sessionmaker(
        bind=async_engine, class_=AsyncSession, expire_on_commit=False
    )
    async with session_maker() as session:
        yield session
        await session.rollback()
