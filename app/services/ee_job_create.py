"""Create EE job from JSON object payload (stored as JSONB)."""

from __future__ import annotations

import logging
import uuid
from typing import Any

from sqlalchemy.orm import Session

from app.models.enums import JobStatus, JobType, TokenType
from app.models.jobs import Job, JobDetailsEE
from app.models.users import User
from app.services.job_token_debit import InsufficientTokensError, debit_job_tokens, ee_submit_token_cost

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
        for key in ("projectName", "insuredName", "claimNumber"):
            val = pd.get(key)
            if isinstance(val, str) and val.strip():
                display_name = val.strip()
                break

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
    cost = ee_submit_token_cost()
    try:
        db.flush()
        debit_job_tokens(
            db,
            wallet_user_id=user.id,
            job_id=job_id,
            token_type=TokenType.EE,
            amount=cost,
        )
        db.commit()
    except InsufficientTokensError:
        db.rollback()
        raise
    except Exception:
        db.rollback()
        logger.exception("Failed to commit EE job")
        raise
    db.refresh(job)
    return job
