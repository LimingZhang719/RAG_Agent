from __future__ import annotations

from app.core.config import settings


def build_vector_store_config() -> dict[str, str]:
    return {
        "schema": settings.pgvector_schema,
        "table_name": settings.pgvector_table,
    }
