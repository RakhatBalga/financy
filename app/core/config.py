"""Application configuration via Pydantic Settings.

All runtime configuration is read from environment variables (or a local
``.env`` file). Import the module-level :data:`settings` singleton everywhere
instead of reading ``os.environ`` directly.
"""

from __future__ import annotations

from functools import cached_property

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Strongly-typed application settings.

    Values are loaded from environment variables; unknown variables are
    ignored so the same ``.env`` can be shared with docker-compose.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # --- Telegram ---
    bot_token: str = Field(alias="BOT_TOKEN")
    webhook_url: str = Field(default="", alias="WEBHOOK_URL")
    webhook_path: str = Field(default="/webhook", alias="WEBHOOK_PATH")
    webhook_secret: str = Field(default="", alias="WEBHOOK_SECRET")
    webapp_host: str = Field(default="0.0.0.0", alias="WEBAPP_HOST")
    webapp_port: int = Field(default=8080, alias="WEBAPP_PORT")

    # --- Database ---
    postgres_user: str = Field(default="finance", alias="POSTGRES_USER")
    postgres_password: str = Field(default="finance", alias="POSTGRES_PASSWORD")
    postgres_db: str = Field(default="finance", alias="POSTGRES_DB")
    postgres_host: str = Field(default="localhost", alias="POSTGRES_HOST")
    postgres_port: int = Field(default=5432, alias="POSTGRES_PORT")

    # --- Redis ---
    redis_host: str = Field(default="localhost", alias="REDIS_HOST")
    redis_port: int = Field(default=6379, alias="REDIS_PORT")
    redis_db: int = Field(default=0, alias="REDIS_DB")

    # --- Gemini ---
    gemini_api_key: str = Field(default="", alias="GEMINI_API_KEY")
    gemini_model: str = Field(
        default="gemini-3.1-pro-preview", alias="GEMINI_MODEL"
    )

    # --- App ---
    default_currency: str = Field(default="KZT", alias="DEFAULT_CURRENCY")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    tz: str = Field(default="Asia/Almaty", alias="TZ")

    @cached_property
    def database_url(self) -> str:
        """Async SQLAlchemy DSN (asyncpg driver)."""
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @cached_property
    def alembic_database_url(self) -> str:
        """Sync DSN for Alembic migrations (psycopg driver not needed at runtime).

        Alembic runs its own async engine in ``env.py``, so we reuse the async
        DSN. Exposed separately in case a sync driver is preferred later.
        """
        return self.database_url

    @cached_property
    def redis_url(self) -> str:
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"

    @property
    def use_webhook(self) -> bool:
        """Run via webhook when a public URL is configured, else long-polling."""
        return bool(self.webhook_url)


settings = Settings()  # type: ignore[call-arg]
