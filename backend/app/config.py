"""Application configuration loaded from environment variables.

All settings are declared as fields on `Settings`. Access them through
`get_settings()` so the parsing cost is paid once.
"""

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Typed view of the backend environment.

    Mirrors `.env.example` at the repo root. Missing required values fail loudly
    on first access via `get_settings()`.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    anthropic_api_key: str = Field(..., description="Anthropic API key for Opus and Sonnet.")
    database_url: str = Field(..., description="Postgres async DSN (postgresql+asyncpg://...).")
    redis_url: str = Field(..., description="Redis DSN (redis://...).")
    edgar_user_agent: str = Field(
        ...,
        description="Contact User-Agent for SEC EDGAR ('Name email').",
    )
    newsapi_key: str = Field("", description="NewsAPI key. Optional in dev; required in prod.")

    max_daily_llm_cost_usd: float = Field(10.00, ge=0.0)
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    environment: Literal["dev", "ci", "staging", "prod"] = "dev"
    llm_cache_dir: Path = Field(Path("./.llm_cache"))

    logfire_token: str = ""
    sentry_dsn: str = ""

    finnhub_api_key: str = ""
    slack_webhook_url: str = ""


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return the parsed settings singleton."""
    return Settings()
