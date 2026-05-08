"""
Application configuration.
Loads environment variables via pydantic-settings.

Minimal version for task 03 — expand in task 06.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ── Vexa.ai ────────────────────────────────────────────────
    VEXA_API_KEY: str = ""
    VEXA_API_BASE: str = "https://api.cloud.vexa.ai"

    # ── OpenRouter ─────────────────────────────────────────────
    OPENROUTER_API_KEY: str = ""
    OPENROUTER_MODEL: str = "anthropic/claude-sonnet-4-7-20250514"

    # ── App ─────────────────────────────────────────────────────
    MEETY_API_KEY: str = ""  # Set this in production!
    APP_BASE_URL: str = "http://localhost:8080"
    DATABASE_URL: str = "sqlite:///./meety.db"
    LOG_LEVEL: str = "INFO"


settings = Settings()
