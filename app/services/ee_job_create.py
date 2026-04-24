"""Create EE job from JSON object payload (stored as JSONB)."""

from __future__ import annotations

import logging
import uuid
from typing import Any

from sqlalchemy.orm import Session

from app.models.enums import JobStatus, JobType
from app.models.jobs import Job, JobDetailsEE
from app.models.users import User

logger = logging.getLogger(__name__)


def create_ee_job_from_payload(
    db: Session,
    *,
    user: User,
    payload: dict[str, Any],
) -> Job:
    job_id = uuid.uuid4()
    display_name: str | None = None
    pd = payload.get("projectDetails")
    if isinstance(pd, dict):
        pn = pd.get("projectName")
        if isinstance(pn, str) and pn.strip():
            display_name = pn.strip()

    job = Job(
        id=job_id,
        user_id=user.id,
        job_type=JobType.EE,
        status=JobStatus.CONFIRMED,
        original_filename=display_name,
    )
    details = JobDetailsEE(job_id=job_id, payload=payload)
    db.add(job)
    db.add(details)
    try:
        db.commit()
    except Exception:
        db.rollback()
        logger.exception("Failed to commit EE job")
        raise
    db.refresh(job)
    return job
