from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# Resolve .env from project root (parent of `app/`) so loading works regardless of cwd.
_ENV_FILE = Path(__file__).resolve().parents[2] / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=_ENV_FILE, env_file_encoding="utf-8", extra="ignore")

    app_env: str = Field(
        default="production",
        description=(
            "Application environment: development/dev/local expose richer API errors, "
            "stub token helpers, and Swagger/OpenAPI docs; production disables those docs."
        ),
    )

    database_url: str | None = Field(default=None, description="Postgres connection string (pooler is fine for the app).")
    direct_url: str | None = Field(default=None, description="Direct Postgres URL for migrations / DDL if needed.")

    supabase_url: str | None = Field(
        default=None,
        description="Project URL (Dashboard → API). Required to verify ES256/RS256 access tokens (JWKS).",
    )
    supabase_jwt_secret: str | None = Field(
        default=None,
        description="JWT secret (Dashboard → API → JWT Secret). Only used for HS256 tokens.",
    )
    supabase_service_role_key: str | None = Field(
        default=None,
        description="Service role key — server-only; Storage signed URLs and Admin API.",
    )
    supabase_storage_bucket_ff_input: str | None = Field(
        default=None,
        description="Fast Fill input bucket — presigned uploads (user PDFs / source files).",
    )
    supabase_storage_bucket_ff_samples: str | None = Field(
        default=None,
        description="Fast Fill sample/reference uploads only — not sent through normal FF job pipeline; presign via sample-upload endpoint.",
    )
    supabase_storage_bucket_ff_output: str | None = Field(
        default=None,
        description="Fast Fill output bucket — generated files / exports.",
    )
    supabase_storage_bucket_ee_readable: str | None = Field(
        default=None,
        description=(
            "Express estimate readable renders only — server-written `payload.md` per job. "
            "If unset, `supabase_storage_bucket_ee_output` then FF output bucket is used."
        ),
    )
    supabase_storage_bucket_ee_output: str | None = Field(
        default=None,
        description=(
            "Express estimate final artifacts — presigned operator uploads and `output_file_key` downloads. "
            "If unset, FF output bucket is used for those URLs."
        ),
    )
    storage_signed_download_ttl_seconds: int = Field(
        default=3600,
        ge=60,
        le=604800,
        description="Lifetime (seconds) for on-the-fly signed download URLs in job list responses.",
    )

    cors_origins: str = Field(
        default="",
        description="Comma-separated browser origins allowed for CORS (e.g. http://localhost:5173,https://app.example.com). Empty = no CORS middleware.",
    )

    stub_token_credit_enabled: bool = Field(
        default=False,
        description="When true and app_env is development-like, POST /api/v1/tokens/stub/credit adds tokens without Stripe.",
    )

    app_session_max_age_seconds: int = Field(
        default=86400,
        ge=0,
        description=(
            "Max age of app session from users.last_login_at (set by POST /api/v1/session/start). "
            "0 disables the check; otherwise expired/null last_login_at yields 401 app_session_expired."
        ),
    )
    app_session_start_min_interval_seconds: int = Field(
        default=60,
        ge=0,
        description=(
            "Minimum seconds between POST /api/v1/session/start for the same user "
            "(based on last_login_at). 0 disables. Exceeded → 429 session_start_rate_limited."
        ),
    )

    ee_job_submit_token_cost: int = Field(
        default=1,
        ge=0,
        description="Express Estimate (EE) tokens debited on POST /jobs/ee. Set 0 to skip debit (not recommended in production).",
    )
    ff_job_submit_token_cost: int = Field(
        default=1,
        ge=0,
        description="Fast Fill (FF) tokens debited when submitting draft job details (draft → confirmed). Set 0 to skip.",
    )

    @property
    def is_development(self) -> bool:
        return (self.app_env or "").strip().lower() in ("development", "dev", "local")


@lru_cache
def get_settings() -> Settings:
    return Settings()
