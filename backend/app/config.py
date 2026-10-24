"""Application settings, loaded from environment variables (hard rule 4).

Never hard-code secrets here. Locally they come from `.env`; in production they
come from Render environment variables. `.env.example` documents every key.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Typed, validated application configuration."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # --- App ---
    environment: Literal["development", "test", "production"] = "development"
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    # --- LLM ---
    # auto = Gemini when a key is present, otherwise the offline fake adapter.
    llm_provider: Literal["auto", "gemini", "fake"] = "auto"
    gemini_api_key: str = ""
    gemini_model: str = "gemini-1.5-flash"

    # --- Database (backend only) ---
    # auto = Supabase when configured, otherwise the local SQLite store.
    data_backend: Literal["auto", "local", "supabase"] = "auto"
    local_db_path: str = ".data/app.db"
    supabase_url: str = ""
    supabase_service_key: str = ""

    # --- Guardrails ---
    # Hard rule 3: cap tool calls per investigation, enforced in the agent loop.
    max_tool_calls: int = 8
    # Hard rule: cap pasted message length to keep prompts inside free-tier quotas.
    max_message_chars: int = 8000
    rate_limit_per_minute: int = 30
    # Below this length the agent asks a clarifying question instead of guessing.
    min_assessable_chars: int = 25

    @property
    def cors_origin_list(self) -> list[str]:
        """`CORS_ORIGINS` split into a clean list of origins."""
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def database_configured(self) -> bool:
        """True when both Supabase values are present (used by /api/health)."""
        return bool(self.supabase_url and self.supabase_service_key)

    @property
    def resolved_data_backend(self) -> Literal["local", "supabase"]:
        """Concrete storage backend: Supabase only when explicitly configured."""
        if self.data_backend == "supabase":
            return "supabase"
        if self.data_backend == "local":
            return "local"
        return "supabase" if self.database_configured else "local"

    @property
    def resolved_llm_provider(self) -> Literal["gemini", "fake"]:
        """Concrete LLM provider: Gemini only when a key is present."""
        if self.llm_provider == "gemini":
            return "gemini"
        if self.llm_provider == "fake":
            return "fake"
        return "gemini" if self.gemini_api_key else "fake"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return the process-wide settings singleton (cached)."""
    return Settings()
