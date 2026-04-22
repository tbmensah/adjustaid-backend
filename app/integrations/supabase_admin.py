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


def create_signed_upload_url(bucket: str, object_path: str) -> dict[str, Any]:
    """Presigned upload URL with upsert so re-upload same path overwrites object."""
    sb = get_supabase_service_client()
    path = object_path.strip().lstrip("/")
    return sb.storage.from_(bucket).create_signed_upload_url(
        path,
        options=CreateSignedUploadUrlOptions(upsert="true"),
    )


def create_ff_signed_upload_url(input_bucket: str, object_path: str) -> dict[str, Any]:
    """Presigned upload URL with upsert so re-upload same path overwrites object."""
    return create_signed_upload_url(input_bucket, object_path)


def upload_bytes(
    bucket: str,
    object_path: str,
    data: bytes,
    content_type: str,
    *,
    upsert: bool = True,
) -> None:
    """Upload raw bytes to Storage (service role)."""
    sb = get_supabase_service_client()
    path = object_path.strip().lstrip("/")
    opts: dict[str, str] = {"content-type": content_type}
    if upsert:
        opts["upsert"] = "true"
    # storage3 2.28 treats BytesIO as a path (calls open()); raw bytes is supported.
    sb.storage.from_(bucket).upload(path, data, file_options=opts)


def _split_storage_object_path(object_path: str) -> tuple[str, str]:
    """Return (folder_prefix, file_name) for Storage list(). Folder may be empty."""
    path = object_path.strip().lstrip("/")
    if "/" not in path:
        return "", path
    folder, name = path.rsplit("/", 1)
    return folder, name


def object_exists(bucket: str, object_path: str) -> bool:
    """True if an object exists at path."""
    sb = get_supabase_service_client()
    path = object_path.strip().lstrip("/")
    bucket_api = sb.storage.from_(bucket)
    exists_fn = getattr(bucket_api, "exists", None)
    if callable(exists_fn):
        try:
            return bool(exists_fn(path))
        except Exception:
            pass
    folder, name = _split_storage_object_path(path)
    try:
        items = bucket_api.list(folder or "")
    except Exception:
        return False
    return any(it.get("name") == name for it in items or [])


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
