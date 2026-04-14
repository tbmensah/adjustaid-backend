from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# Resolve .env from project root (parent of `app/`) so loading works regardless of cwd.
_ENV_FILE = Path(__file__).resolve().parents[2] / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=_ENV_FILE, env_file_encoding="utf-8", extra="ignore")

    database_url: str | None = Field(default=None, description="Postgres connection string (pooler is fine for the app).")
    direct_url: str | None = Field(default=None, description="Direct Postgres URL for migrations / DDL if needed.")

    supabase_url: str | None = Field(default=None, description="Project URL (Dashboard → API → Project URL).")
    supabase_jwt_secret: str | None = Field(
        default=None,
        description="JWT secret — verify Supabase access tokens (Dashboard → API → JWT Secret).",
    )
    supabase_service_role_key: str | None = Field(
        default=None,
        description="Optional. Service role key for Admin API or server-side Supabase client (keep server-only).",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
