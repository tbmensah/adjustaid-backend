"""Supabase client using service role (server-only)."""

from __future__ import annotations

from functools import lru_cache
from typing import Any

from storage3.types import CreateSignedUploadUrlOptions
from supabase import Client, create_client

from app.core.config import get_settings


@lru_cache(maxsize=1)
def get_supabase_service_client() -> Client:
    settings = get_settings()
    url = (settings.supabase_url or "").rstrip("/")
    key = settings.supabase_service_role_key
    if not url or not key:
        msg = "SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set for Storage operations"
        raise RuntimeError(msg)
    return create_client(url, key)


def create_ff_signed_upload_url(input_bucket: str, object_path: str) -> dict[str, Any]:
    """Presigned upload URL with upsert so re-upload same path overwrites object."""
    sb = get_supabase_service_client()
    return sb.storage.from_(input_bucket).create_signed_upload_url(
        object_path,
        options=CreateSignedUploadUrlOptions(upsert="true"),
    )
