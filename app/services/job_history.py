"""List jobs for a user with filters and pagination."""

from __future__ import annotations

import logging
from datetime import datetime

from sqlalchemy import Select, and_, func, select
from sqlalchemy.orm import Session, selectinload

from app.core.config import get_settings
from app.integrations.supabase_admin import create_signed_download_url
from app.models.enums import JobStatus, JobType
from app.models.jobs import Job
from app.models.users import User
from app.schemas.job_history import JobHistoryItem

logger = logging.getLogger(__name__)


def _token_cost(job: Job) -> int:
    return 1 if job.status == JobStatus.COMPLETED else 0


def _output_object_key(job: Job) -> str | None:
    if job.job_type == JobType.FF and job.details_ff is not None and job.details_ff.output_file_key:
        return job.details_ff.output_file_key.strip()
    if job.job_type == JobType.EE and job.details_ee is not None and job.details_ee.output_file_key:
        return job.details_ee.output_file_key.strip()
    return None


def _output_bucket_for_job_type(job_type: JobType) -> str | None:
    s = get_settings()
    if job_type == JobType.FF:
        return s.supabase_storage_bucket_ff_output
    return s.supabase_storage_bucket_ee_output or s.supabase_storage_bucket_ff_output


def _download_url_for_job(job: Job) -> str | None:
    key = _output_object_key(job)
    if not key:
        return None
    bucket = _output_bucket_for_job_type(job.job_type)
    if not bucket:
        return None
    ttl = get_settings().storage_signed_download_ttl_seconds
    try:
        return create_signed_download_url(bucket, key, expires_in=ttl)
    except Exception:
        logger.warning("Signed download URL failed for job_id=%s", job.id, exc_info=True)
        return None


def _to_item(job: Job) -> JobHistoryItem:
    ff_type = None
    if job.job_type == JobType.FF and job.details_ff is not None:
        ff_type = job.details_ff.ff_pdf_type
    return JobHistoryItem(
        id=job.id,
        job_type=job.job_type,
        status=job.status,
        original_filename=job.original_filename,
        created_at=job.created_at,
        updated_at=job.updated_at,
        completed_at=job.completed_at,
        error_message=job.error_message,
        ff_pdf_type=ff_type,
        token_cost=_token_cost(job),
        download_url=_download_url_for_job(job),
    )


def list_user_jobs(
    db: Session,
    *,
    user: User,
    job_type: JobType | None = None,
    status: list[JobStatus] | None = None,
    created_from: datetime | None = None,
    created_to: datetime | None = None,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[JobHistoryItem], int]:
    conditions = [Job.user_id == user.id]
    if job_type is not None:
        conditions.append(Job.job_type == job_type)
    if status:
        conditions.append(Job.status.in_(status))
    if created_from is not None:
        conditions.append(Job.created_at >= created_from)
    if created_to is not None:
        conditions.append(Job.created_at <= created_to)

    filt = and_(*conditions)

    count_stmt = select(func.count()).select_from(Job).where(filt)
    total = db.scalar(count_stmt) or 0

    offset = (page - 1) * page_size
    list_stmt: Select[tuple[Job]] = (
        select(Job)
        .where(filt)
        .options(selectinload(Job.details_ff), selectinload(Job.details_ee))
        .order_by(Job.created_at.desc())
        .offset(offset)
        .limit(page_size)
    )
    rows = db.scalars(list_stmt).all()
    items = [_to_item(j) for j in rows]
    return items, total


def _like_pattern(q: str) -> str:
    """Escape LIKE wildcards in user input."""
    s = q.strip()
    for a, b in (("\\", "\\\\"), ("%", "\\%"), ("_", "\\_")):
        s = s.replace(a, b)
    return f"%{s}%"


def search_user_jobs_by_original_filename(
    db: Session,
    *,
    user: User,
    q: str,
    job_type: JobType | None = None,
    status: list[JobStatus] | None = None,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[JobHistoryItem], int]:
    """Match `jobs.original_filename` with ILIKE substring (scoped to user)."""
    conditions = [
        Job.user_id == user.id,
        Job.original_filename.is_not(None),
        Job.original_filename.ilike(_like_pattern(q), escape="\\"),
    ]
    if job_type is not None:
        conditions.append(Job.job_type == job_type)
    if status:
        conditions.append(Job.status.in_(status))

    filt = and_(*conditions)

    count_stmt = select(func.count()).select_from(Job).where(filt)
    total = db.scalar(count_stmt) or 0

    offset = (page - 1) * page_size
    list_stmt: Select[tuple[Job]] = (
        select(Job)
        .where(filt)
        .options(selectinload(Job.details_ff), selectinload(Job.details_ee))
        .order_by(Job.created_at.desc())
        .offset(offset)
        .limit(page_size)
    )
    rows = db.scalars(list_stmt).all()
    items = [_to_item(j) for j in rows]
    return items, total
