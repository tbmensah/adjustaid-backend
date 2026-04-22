"""List jobs for a user with filters and pagination."""

from __future__ import annotations

import logging
import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import Select, and_, exists, func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.core.config import get_settings
from app.integrations.supabase_admin import create_signed_download_url
from app.models.enums import JobStatus, JobType
from app.models.jobs import Job, JobDetailsEE, JobDetailsFF
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


def _ee_has_output_file():
    return exists(
        select(1)
        .select_from(JobDetailsEE)
        .where(
            JobDetailsEE.job_id == Job.id,
            JobDetailsEE.output_file_key.isnot(None),
            JobDetailsEE.output_file_key != "",
        )
    )


def _ff_has_output_file():
    return exists(
        select(1)
        .select_from(JobDetailsFF)
        .where(
            JobDetailsFF.job_id == Job.id,
            JobDetailsFF.output_file_key.isnot(None),
            JobDetailsFF.output_file_key != "",
        )
    )


def _to_item(job: Job) -> JobHistoryItem:
    ff_type = None
    if job.job_type == JobType.FF and job.details_ff is not None:
        ff_type = job.details_ff.ff_pdf_type
    return JobHistoryItem(
        id=job.id,
        owner_id=job.user_id,
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


def _list_jobs_paginated(
    db: Session,
    *,
    owner_user_id: uuid.UUID | None,
    job_type: JobType | None = None,
    status: list[JobStatus] | None = None,
    created_from: datetime | None = None,
    created_to: datetime | None = None,
    has_output: bool | None = None,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[JobHistoryItem], int]:
    """`owner_user_id` set → that user's jobs only; `None` → all users (ops)."""
    conditions: list[Any] = [Job.status != JobStatus.DRAFT]
    if owner_user_id is not None:
        conditions.append(Job.user_id == owner_user_id)
    if job_type is not None:
        conditions.append(Job.job_type == job_type)
    if status:
        conditions.append(Job.status.in_(status))
    if created_from is not None:
        conditions.append(Job.created_at >= created_from)
    if created_to is not None:
        conditions.append(Job.created_at <= created_to)
    if has_output is True:
        conditions.append(
            or_(
                and_(Job.job_type == JobType.EE, _ee_has_output_file()),
                and_(Job.job_type == JobType.FF, _ff_has_output_file()),
            )
        )
    elif has_output is False:
        conditions.append(
            or_(
                and_(Job.job_type == JobType.EE, ~_ee_has_output_file()),
                and_(Job.job_type == JobType.FF, ~_ff_has_output_file()),
            )
        )

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


def list_user_jobs(
    db: Session,
    *,
    user: User,
    job_type: JobType | None = None,
    status: list[JobStatus] | None = None,
    created_from: datetime | None = None,
    created_to: datetime | None = None,
    has_output: bool | None = None,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[JobHistoryItem], int]:
    return _list_jobs_paginated(
        db,
        owner_user_id=user.id,
        job_type=job_type,
        status=status,
        created_from=created_from,
        created_to=created_to,
        has_output=has_output,
        page=page,
        page_size=page_size,
    )


def list_all_jobs_for_ops(
    db: Session,
    *,
    job_type: JobType | None = None,
    status: list[JobStatus] | None = None,
    created_from: datetime | None = None,
    created_to: datetime | None = None,
    has_output: bool | None = None,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[JobHistoryItem], int]:
    """All customers' jobs (non-draft). Caller must enforce back-office auth."""
    return _list_jobs_paginated(
        db,
        owner_user_id=None,
        job_type=job_type,
        status=status,
        created_from=created_from,
        created_to=created_to,
        has_output=has_output,
        page=page,
        page_size=page_size,
    )


def _like_pattern(q: str) -> str:
    """Escape LIKE wildcards in user input."""
    s = q.strip()
    for a, b in (("\\", "\\\\"), ("%", "\\%"), ("_", "\\_")):
        s = s.replace(a, b)
    return f"%{s}%"


def _search_jobs_by_filename_paginated(
    db: Session,
    *,
    owner_user_id: uuid.UUID | None,
    q: str,
    job_type: JobType | None = None,
    status: list[JobStatus] | None = None,
    created_from: datetime | None = None,
    created_to: datetime | None = None,
    has_output: bool | None = None,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[JobHistoryItem], int]:
    conditions = [
        Job.status != JobStatus.DRAFT,
        Job.original_filename.is_not(None),
        Job.original_filename.ilike(_like_pattern(q), escape="\\"),
    ]
    if owner_user_id is not None:
        conditions.append(Job.user_id == owner_user_id)
    if job_type is not None:
        conditions.append(Job.job_type == job_type)
    if status:
        conditions.append(Job.status.in_(status))
    if created_from is not None:
        conditions.append(Job.created_at >= created_from)
    if created_to is not None:
        conditions.append(Job.created_at <= created_to)
    if has_output is True:
        conditions.append(
            or_(
                and_(Job.job_type == JobType.EE, _ee_has_output_file()),
                and_(Job.job_type == JobType.FF, _ff_has_output_file()),
            )
        )
    elif has_output is False:
        conditions.append(
            or_(
                and_(Job.job_type == JobType.EE, ~_ee_has_output_file()),
                and_(Job.job_type == JobType.FF, ~_ff_has_output_file()),
            )
        )

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


def search_user_jobs_by_original_filename(
    db: Session,
    *,
    user: User,
    q: str,
    job_type: JobType | None = None,
    status: list[JobStatus] | None = None,
    created_from: datetime | None = None,
    created_to: datetime | None = None,
    has_output: bool | None = None,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[JobHistoryItem], int]:
    """Match `jobs.original_filename` with ILIKE substring (signed-in user's jobs only)."""
    return _search_jobs_by_filename_paginated(
        db,
        owner_user_id=user.id,
        q=q,
        job_type=job_type,
        status=status,
        created_from=created_from,
        created_to=created_to,
        has_output=has_output,
        page=page,
        page_size=page_size,
    )


def search_all_jobs_for_ops(
    db: Session,
    *,
    q: str,
    job_type: JobType | None = None,
    status: list[JobStatus] | None = None,
    created_from: datetime | None = None,
    created_to: datetime | None = None,
    has_output: bool | None = None,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[JobHistoryItem], int]:
    """Search all customers' jobs by filename. Caller must enforce back-office auth."""
    return _search_jobs_by_filename_paginated(
        db,
        owner_user_id=None,
        q=q,
        job_type=job_type,
        status=status,
        created_from=created_from,
        created_to=created_to,
        has_output=has_output,
        page=page,
        page_size=page_size,
    )
