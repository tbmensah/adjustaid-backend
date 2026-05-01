"""Mint new signed upload URL for existing FF job (same object path)."""

from __future__ import annotations

import logging
import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.integrations.supabase_admin import create_ff_signed_upload_url
from app.models.enums import JobStatus, JobType, UserType
from app.models.jobs import Job, JobDetailsFF
from app.models.users import User

logger = logging.getLogger(__name__)

_ALLOWED = frozenset({JobStatus.DRAFT, JobStatus.CONFIRMED})


class RefreshFfUploadNotFound(Exception):
    pass


class RefreshFfUploadConflict(Exception):
    def __init__(self, detail: str) -> None:
        self.detail = detail


def _object_path_for_job(job: Job, job_id: uuid.UUID, details: JobDetailsFF | None) -> str:
    """
    Always return a path under `{owner_id}/`. Stored `pdf_file_key` is treated as untrusted
    (could be a stale or attacker-controlled value from before validation was added) and is
    used only when it lives in the job owner's namespace; otherwise we fall back to the
    canonical draft-intent path.
    """
    default = f"{job.user_id}/{job_id}"
    raw = (details.pdf_file_key or "").strip().lstrip("/") if details is not None else ""
    if not raw:
        return default
    if ".." in raw.split("/"):
        return default
    if not raw.startswith(f"{job.user_id}/"):
        return default
    return raw


def refresh_ff_upload_url(
    db: Session,
    *,
    user: User,
    job_id: uuid.UUID,
    input_bucket: str,
) -> tuple[uuid.UUID, str, str]:
    stmt = select(Job).where(
        Job.id == job_id,
        Job.job_type == JobType.FF,
    )
    if user.user_type != UserType.BACK_OFFICE:
        stmt = stmt.where(Job.user_id == user.id)
    job = db.scalar(stmt)
    if job is None:
        raise RefreshFfUploadNotFound()

    if job.status not in _ALLOWED:
        raise RefreshFfUploadConflict("Job no longer accepts upload refresh (wrong status)")

    details = db.get(JobDetailsFF, job_id)
    object_path = _object_path_for_job(job, job_id, details)

    try:
        signed = create_ff_signed_upload_url(input_bucket, object_path)
    except Exception:
        logger.exception(
            "Supabase create_signed_upload_url (refresh) failed bucket=%s path=%s",
            input_bucket,
            object_path,
        )
        raise

    upload_url = signed.get("signed_url") or signed.get("signedUrl") or ""
    if not upload_url:
        raise RuntimeError("Storage API returned no signed URL")

    return job_id, object_path, upload_url
