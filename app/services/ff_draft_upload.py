"""Create FF draft job (id only) + Supabase signed upload URL — details row comes with later payload."""

from __future__ import annotations

import logging
import uuid

from sqlalchemy.orm import Session

from app.integrations.supabase_admin import create_ff_signed_upload_url
from app.models.enums import JobStatus, JobType
from app.models.jobs import Job
from app.models.users import User

logger = logging.getLogger(__name__)


def create_ff_draft_upload_intent(
    db: Session,
    *,
    user: User,
    input_bucket: str,
) -> tuple[uuid.UUID, str, str]:
    """
    Allocate job_id, presign upload for object named by that id, insert draft `jobs` row only.

    Storage object path: `{user_id}/{job_id}` (basename is the job id string).

    Returns (job_id, storage_object_path, signed_upload_url).
    """
    job_id = uuid.uuid4()
    object_path = f"{user.id}/{job_id}"

    try:
        signed = create_ff_signed_upload_url(input_bucket, object_path)
    except Exception:
        logger.exception(
            "Supabase create_signed_upload_url failed bucket=%s path=%s",
            input_bucket,
            object_path,
        )
        raise

    upload_url = signed.get("signed_url") or signed.get("signedUrl") or ""
    if not upload_url:
        msg = "Storage API returned no signed URL"
        raise RuntimeError(msg)

    job = Job(
        id=job_id,
        user_id=user.id,
        job_type=JobType.FF,
        status=JobStatus.DRAFT,
        original_filename=None,
    )
    db.add(job)
    try:
        db.commit()
    except Exception:
        db.rollback()
        logger.exception("Failed to commit FF draft job job_id=%s", job_id)
        raise

    return job_id, object_path, upload_url
