"""Submit FF job details (job_details_ff + status transition)."""

from __future__ import annotations

import logging
import uuid

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.enums import JobStatus, JobType
from app.models.jobs import Job, JobDetailsFF
from app.models.users import User
from app.schemas.ff_job import FfJobDetailsRequest

logger = logging.getLogger(__name__)


class SubmitFfJobDetailsNotFound(Exception):
    """No FF job for this user / id."""


class SubmitFfJobDetailsConflict(Exception):
    def __init__(self, detail: str) -> None:
        self.detail = detail


def submit_ff_job_details(
    db: Session,
    *,
    user: User,
    job_id: uuid.UUID,
    body: FfJobDetailsRequest,
) -> Job:
    job = db.scalar(
        select(Job).where(
            Job.id == job_id,
            Job.user_id == user.id,
            Job.job_type == JobType.FF,
        )
    )
    if job is None:
        raise SubmitFfJobDetailsNotFound()

    if job.status != JobStatus.DRAFT:
        raise SubmitFfJobDetailsConflict("Job is not editable (must be draft)")

    existing = db.get(JobDetailsFF, job_id)
    if existing is not None:
        raise SubmitFfJobDetailsConflict("Job details already submitted")

    default_pdf_key = f"{user.id}/{job_id}"
    pdf_key = body.pdf_file_key.strip() if body.pdf_file_key else default_pdf_key
    if not pdf_key:
        pdf_key = default_pdf_key

    job.original_filename = body.original_filename

    details = JobDetailsFF(
        job_id=job_id,
        ff_pdf_type=body.ff_pdf_type,
        pdf_file_key=pdf_key,
        esx_file_key=body.esx_file_key.strip() if body.esx_file_key else None,
    )
    job.status = JobStatus.CONFIRMED
    db.add(details)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise SubmitFfJobDetailsConflict("Job details already submitted") from None
    except Exception:
        db.rollback()
        logger.exception("commit ff job details failed job_id=%s", job_id)
        raise

    db.refresh(job)
    return job
