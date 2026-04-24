"""Presigned uploads for sample/reference files — separate bucket from production FF input."""

from __future__ import annotations

import logging
import uuid

from app.integrations.supabase_admin import create_ff_signed_upload_url
from app.models.users import User

logger = logging.getLogger(__name__)


def create_ff_sample_upload_url(*, user: User, samples_bucket: str) -> tuple[str, str]:
    """
    Build `{user_id}/samples/{uuid}` and return (storage_path, signed_upload_url).

    No `jobs` row — client uses this only for non-pipeline sample data.
    """
    object_path = f"{user.id}/samples/{uuid.uuid4()}"
    try:
        signed = create_ff_signed_upload_url(samples_bucket, object_path)
    except Exception:
        logger.exception(
            "Supabase sample signed upload failed bucket=%s path=%s",
            samples_bucket,
            object_path,
        )
        raise

    upload_url = signed.get("signed_url") or signed.get("signedUrl") or ""
    if not upload_url:
        msg = "Storage API returned no signed URL"
        raise RuntimeError(msg)
    return object_path, upload_url
