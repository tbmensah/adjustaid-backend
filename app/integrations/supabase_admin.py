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


def create_signed_download_url(
    bucket: str,
    object_path: str,
    *,
    expires_in: int = 3600,
) -> str:
    """Short-lived read URL for an object in Storage."""
    sb = get_supabase_service_client()
    path = object_path.strip().lstrip("/")
    r = sb.storage.from_(bucket).create_signed_url(path, expires_in)
    url = r.get("signedURL") or r.get("signedUrl") or ""
    if not url:
        msg = "Storage API returned no signed download URL"
        raise RuntimeError(msg)
    return url
