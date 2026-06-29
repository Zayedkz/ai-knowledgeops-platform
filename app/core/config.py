from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_env: str = "local"
    log_level: str = "INFO"
    database_url: str = "postgresql+psycopg://knowledgeops:knowledgeops@localhost:5432/knowledgeops"
    redis_url: str = "redis://localhost:6379/0"
    llm_provider: str = "mock"
    embedding_provider: str = "mock"
    rate_limit_per_minute: int = Field(default=60, ge=1)


@lru_cache
def get_settings() -> Settings:
    return Settings()

