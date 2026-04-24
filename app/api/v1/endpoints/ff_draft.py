from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import current_user
from app.core.config import get_settings
from app.db.session import get_db
from app.models.users import User
from app.schemas.envelope import SuccessEnvelope
from app.schemas.ff_draft import FfDraftUploadData
from app.services.ff_draft_upload import create_ff_draft_upload_intent

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get(
    "/jobs/ff/draft-upload",
    summary="Allocate draft FF job id + presigned upload URL",
    description=(
        "Returns `job_id` and `upload_url` so the client can upload the file and "
        "send the rest of the payload in parallel. Storage object is `{user_id}/{job_id}`. "
        "Set `original_filename` on `POST /jobs/ff/{job_id}/details` with `ff_pdf_type` and keys. "
        "`job_details_ff` is created when that payload is submitted."
    ),
)
def ff_draft_upload_intent(
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
) -> SuccessEnvelope[FfDraftUploadData]:
    settings = get_settings()
    input_bucket = settings.supabase_storage_bucket_ff_input
    if not input_bucket:
        logger.error("SUPABASE_STORAGE_BUCKET_FF_INPUT is not set")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="FF input storage bucket not configured",
        )
    try:
        job_id, storage_path, upload_url = create_ff_draft_upload_intent(
            db,
            user=user,
            input_bucket=input_bucket,
        )
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e),
        ) from e
    except Exception:
        logger.exception("ff_draft_upload_intent failed")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Could not create draft upload",
        ) from None

    return SuccessEnvelope(
        message="Draft upload intent",
        data=FfDraftUploadData(
            job_id=job_id,
            upload_url=upload_url,
            storage_path=storage_path,
        ),
    )
