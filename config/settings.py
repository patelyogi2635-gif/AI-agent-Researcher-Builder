# config/settings.py
# ─────────────────────────────────────────────────────────────────
# Centralised configuration using pydantic-settings.
# All values come from .env — never hard-code secrets.
# ─────────────────────────────────────────────────────────────────
from functools import lru_cache
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application-wide settings loaded from .env"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── LLM ───────────────────────────────────────────────────────
    groq_api_key: str = Field(..., description="Groq API key")
    llm_model: str = Field(
        default="llama-3.3-70b-versatile",
        description="Groq model to use",
    )
    llm_temperature: float = Field(default=0.1, ge=0.0, le=2.0)

    # ── Search ────────────────────────────────────────────────────
    tavily_api_key: str = Field(default="", description="Tavily API key (Phase 2)")
    max_search_results: int = Field(default=5, ge=1, le=20)

    # ── Scraping ──────────────────────────────────────────────────
    max_scrape_pages: int = Field(default=5, ge=1, le=10)
    scrape_timeout_secs: int = Field(default=8, ge=1, le=30)

    # ── Planning graph ────────────────────────────────────────────
    max_plan_steps: int = Field(default=10, ge=1, le=20)

    # ── Research graph ────────────────────────────────────────────
    max_review_loops: int = Field(default=3, ge=1, le=5)

    # ── Logging ───────────────────────────────────────────────────
    log_level: str = Field(default="INFO")

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        allowed = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        upper = v.upper()
        if upper not in allowed:
            raise ValueError(f"log_level must be one of {allowed}")
        return upper


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return a cached Settings singleton."""
    return Settings()