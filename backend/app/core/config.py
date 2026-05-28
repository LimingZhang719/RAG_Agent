from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=("../.env", ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "Agentic RAG Platform"
    app_version: str = "0.1.0"
    environment: str = "development"
    debug: bool = True

    api_host: str = "127.0.0.1"
    api_port: int = 8000
    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:5173"])

    database_url: str = (
        "postgresql+asyncpg://rag_user:rag_password@localhost:5432/rag_agent"
    )
    sync_database_url: str = (
        "postgresql+psycopg://rag_user:rag_password@localhost:5432/rag_agent"
    )
    redis_url: str = "redis://localhost:6379/0"

    minio_endpoint: str = "localhost:9000"
    minio_access_key: str = "minioadmin"
    minio_secret_key: str = "minioadmin"
    minio_secure: bool = False
    minio_bucket: str = "rag-agent"

    model_provider: str = "openai_compatible"
    model_base_url: str = "https://api.example.com/v1"
    model_api_key: str = ""
    llm_model: str = "qwen-plus"
    embedding_model: str = "text-embedding-v3"
    rerank_model: str = "gte-rerank"
    ocr_provider: str = "external_api"

    log_level: str = "INFO"

    @field_validator("cors_origins", mode="before")
    @classmethod
    def split_cors_origins(cls, value: str | list[str]) -> list[str]:
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
