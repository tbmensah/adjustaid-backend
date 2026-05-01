"""Submit FF job details (job_details_ff + status transition)."""

from __future__ import annotations

import logging
import uuid

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.enums import JobStatus, JobType, TokenType, UserType
from app.models.jobs import Job, JobDetailsFF
from app.models.users import User
from app.schemas.ff_job import FfJobDetailsRequest
from app.services.job_token_debit import InsufficientTokensError, debit_job_tokens, ff_submit_token_cost

logger = logging.getLogger(__name__)


class SubmitFfJobDetailsNotFound(Exception):
    """No FF job for this user / id."""


class SubmitFfJobDetailsConflict(Exception):
    def __init__(self, detail: str) -> None:
        self.detail = detail


class SubmitFfJobDetailsBadRequest(Exception):
    """Client supplied an invalid storage path on the FF details body."""

    def __init__(self, detail: str) -> None:
        self.detail = detail


def _normalize_owner_path(raw: str) -> str:
    norm = (raw or "").strip().lstrip("/")
    if not norm or ".." in norm.split("/"):
        msg = "invalid storage path"
        raise ValueError(msg)
    return norm


def _require_pdf_file_key(*, owner_id: uuid.UUID, job_id: uuid.UUID, raw: str | None) -> str:
    """PDF object lives at the canonical draft-intent path; reject any deviation."""
    expected = f"{owner_id}/{job_id}"
    if not raw:
        return expected
    try:
        norm = _normalize_owner_path(raw)
    except ValueError as e:
        raise SubmitFfJobDetailsBadRequest(str(e)) from None
    if norm != expected:
        msg = "pdf_file_key must match the draft-intent path for this job"
        raise SubmitFfJobDetailsBadRequest(msg)
    return norm


def _normalize_esx_file_key(*, owner_id: uuid.UUID, raw: str | None) -> str | None:
    if not raw:
        return None
    try:
        norm = _normalize_owner_path(raw)
    except ValueError as e:
        raise SubmitFfJobDetailsBadRequest(str(e)) from None
    prefix = f"{owner_id}/"
    if not norm.startswith(prefix):
        msg = "esx_file_key must reside under the owner's storage namespace"
        raise SubmitFfJobDetailsBadRequest(msg)
    return norm


def submit_ff_job_details(
    db: Session,
    *,
    user: User,
    job_id: uuid.UUID,
    body: FfJobDetailsRequest,
) -> Job:
    stmt = select(Job).where(
        Job.id == job_id,
        Job.job_type == JobType.FF,
    )
    if user.user_type != UserType.BACK_OFFICE:
        stmt = stmt.where(Job.user_id == user.id)
    job = db.scalar(stmt)
    if job is None:
        raise SubmitFfJobDetailsNotFound()

    if job.status != JobStatus.DRAFT:
        raise SubmitFfJobDetailsConflict("Job is not editable (must be draft)")

    existing = db.get(JobDetailsFF, job_id)
    if existing is not None:
        raise SubmitFfJobDetailsConflict("Job details already submitted")

    owner_id = job.user_id
    pdf_key = _require_pdf_file_key(owner_id=owner_id, job_id=job_id, raw=body.pdf_file_key)
    esx_key = _normalize_esx_file_key(owner_id=owner_id, raw=body.esx_file_key)

    job.original_filename = body.original_filename

    details = JobDetailsFF(
        job_id=job_id,
        ff_pdf_type=body.ff_pdf_type,
        pdf_file_key=pdf_key,
        esx_file_key=esx_key,
    )
    job.status = JobStatus.CONFIRMED
    db.add(details)
    cost = ff_submit_token_cost()
    try:
        db.flush()
        debit_job_tokens(
            db,
            wallet_user_id=owner_id,
            job_id=job_id,
            token_type=TokenType.FF,
            amount=cost,
        )
        db.commit()
    except InsufficientTokensError:
        db.rollback()
        raise
    except IntegrityError:
        db.rollback()
        raise SubmitFfJobDetailsConflict("Job details already submitted") from None
    except Exception:
        db.rollback()
        logger.exception("commit ff job details failed job_id=%s", job_id)
        raise

    db.refresh(job)
    return job
