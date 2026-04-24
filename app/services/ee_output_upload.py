"""EE readable input render + final output presign / confirm (Supabase Storage)."""

from __future__ import annotations

import logging
import os
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.integrations.supabase_admin import (
    create_signed_upload_url,
    object_exists,
    upload_bytes,
)
from app.models.enums import JobStatus, JobType
from app.models.jobs import Job, JobStatusHistory
from app.services.ee_readable_render import render_payload_markdown, render_payload_xlsx_bytes

logger = logging.getLogger(__name__)

ALLOWED_OUTPUT_EXTENSIONS = frozenset({"md", "pdf", "txt", "docx", "xlsx"})


def ee_readable_bucket() -> str:
    """Bucket for server-generated `payload.md` (readable input). Prefer dedicated bucket vs operator output."""
    s = get_settings()
    b = (
        s.supabase_storage_bucket_ee_readable
        or s.supabase_storage_bucket_ee_output
        or s.supabase_storage_bucket_ff_output
        or ""
    ).strip()
    if not b:
        msg = (
            "Set SUPABASE_STORAGE_BUCKET_EE_READABLE (recommended), "
            "or SUPABASE_STORAGE_BUCKET_EE_OUTPUT / SUPABASE_STORAGE_BUCKET_FF_OUTPUT"
        )
        raise RuntimeError(msg)
    return b


def ee_output_bucket() -> str:
    """Bucket for operator-uploaded final EE artifacts (`output.*`)."""
    s = get_settings()
    b = (s.supabase_storage_bucket_ee_output or s.supabase_storage_bucket_ff_output or "").strip()
    if not b:
        msg = "Set SUPABASE_STORAGE_BUCKET_EE_OUTPUT or SUPABASE_STORAGE_BUCKET_FF_OUTPUT"
        raise RuntimeError(msg)
    return b


def build_readable_input_key(user_id: uuid.UUID, job_id: uuid.UUID) -> str:
    return f"ee/{user_id}/{job_id}/payload.md"


def build_readable_input_excel_key(user_id: uuid.UUID, job_id: uuid.UUID) -> str:
    return f"ee/{user_id}/{job_id}/payload.xlsx"


def build_output_key(user_id: uuid.UUID, job_id: uuid.UUID, ext: str) -> str:
    ext_clean = ext.lstrip(".").lower()
    if ext_clean not in ALLOWED_OUTPUT_EXTENSIONS:
        msg = f"Extension not allowed: {ext_clean}"
        raise ValueError(msg)
    return f"ee/{user_id}/{job_id}/output.{ext_clean}"


def _normalize_upload_path(object_path: str) -> str:
    return object_path.strip().lstrip("/")


def store_readable_input(job: Job) -> str:
    """Render payload to markdown + Excel and upload both to EE readable bucket. Returns markdown object path."""
    if job.job_type != JobType.EE or job.details_ee is None:
        msg = "Job is not an EE job with details"
        raise ValueError(msg)
    bucket = ee_readable_bucket()
    key_md = build_readable_input_key(job.user_id, job.id)
    key_xlsx = build_readable_input_excel_key(job.user_id, job.id)
    md = render_payload_markdown(job.details_ee.payload)
    upload_bytes(bucket, key_md, md.encode("utf-8"), "text/markdown; charset=utf-8", upsert=True)
    xlsx = render_payload_xlsx_bytes(job.details_ee.payload)
    upload_bytes(
        bucket,
        key_xlsx,
        xlsx,
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        upsert=True,
    )
    return key_md


def issue_output_upload_url(*, job: Job, filename: str) -> dict[str, Any]:
    """Presign upload for final operator artifact. Returns dict with signed_url, path, token."""
    if job.job_type != JobType.EE:
        msg = "Not an EE job"
        raise ValueError(msg)
    base = os.path.basename(filename.strip())
    if not base or "." not in base:
        msg = "filename must include an extension"
        raise ValueError(msg)
    ext = base.rsplit(".", 1)[-1].lower()
    if ext not in ALLOWED_OUTPUT_EXTENSIONS:
        msg = f"Allowed extensions: {', '.join(sorted(ALLOWED_OUTPUT_EXTENSIONS))}"
        raise ValueError(msg)
    bucket = ee_output_bucket()
    object_path = build_output_key(job.user_id, job.id, ext)
    signed = create_signed_upload_url(bucket, object_path)
    upload_url = signed.get("signed_url") or signed.get("signedUrl") or ""
    if not upload_url:
        raise RuntimeError("Storage API returned no signed upload URL")
    token = signed.get("token")
    return {
        "upload_url": upload_url,
        "object_path": object_path,
        "token": token if isinstance(token, str) else None,
    }


def _expected_path_prefix(user_id: uuid.UUID, job_id: uuid.UUID) -> str:
    return f"ee/{user_id}/{job_id}/"


def confirm_output_upload(db: Session, *, job: Job, object_path: str) -> Job:
    """After client PUT to presigned URL, persist output_file_key. Idempotent if same path."""
    if job.job_type != JobType.EE or job.details_ee is None:
        msg = "Not an EE job"
        raise ValueError(msg)
    norm = _normalize_upload_path(object_path)
    prefix = _expected_path_prefix(job.user_id, job.id)
    if not norm.startswith(prefix) or ".." in norm:
        msg = "object_path does not belong to this job"
        raise ValueError(msg)
    bucket = ee_output_bucket()
    if not object_exists(bucket, norm):
        msg = "Object not found in storage — upload before confirm"
        raise ValueError(msg)

    details = job.details_ee
    if details.output_file_key == norm:
        db.refresh(job)
        return job

    ttl = get_settings().storage_signed_download_ttl_seconds
    details.output_file_key = norm
    details.output_expires_at = datetime.now(timezone.utc) + timedelta(seconds=ttl)
    db.add(
        JobStatusHistory(
            job_id=job.id,
            from_status=JobStatus.CONFIRMED,
            to_status=JobStatus.CONFIRMED,
            note="output uploaded",
        )
    )
    db.commit()
    db.refresh(job)
    return job


def input_render_exists(job: Job) -> bool:
    if job.job_type != JobType.EE:
        return False
    try:
        bucket = ee_readable_bucket()
    except RuntimeError:
        return False
    key = build_readable_input_key(job.user_id, job.id)
    return object_exists(bucket, key)


def input_render_excel_exists(job: Job) -> bool:
    if job.job_type != JobType.EE:
        return False
    try:
        bucket = ee_readable_bucket()
    except RuntimeError:
        return False
    key = build_readable_input_excel_key(job.user_id, job.id)
    return object_exists(bucket, key)


def ensure_readable_input_excel(job: Job) -> bool:
    """If `payload.md` exists but `payload.xlsx` is missing, generate and upload Excel (legacy backfill)."""
    if job.job_type != JobType.EE or job.details_ee is None:
        return False
    if input_render_excel_exists(job):
        return True
    if not input_render_exists(job):
        return False
    bucket = ee_readable_bucket()
    key = build_readable_input_excel_key(job.user_id, job.id)
    xlsx = render_payload_xlsx_bytes(job.details_ee.payload)
    upload_bytes(
        bucket,
        key,
        xlsx,
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        upsert=True,
    )
    return True
