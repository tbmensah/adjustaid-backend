from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import current_user
from app.core.config import get_settings
from app.models.users import User
from app.schemas.envelope import SuccessEnvelope
from app.schemas.ff_samples import FfSampleUploadData
from app.services.ff_sample_upload import create_ff_sample_upload_url

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get(
    "/jobs/ff/sample-upload",
    summary="Presigned upload URL for FF sample / reference files",
    description=(
        "Separate from `GET /jobs/ff/draft-upload`. No job row. "
        "Client PUTs file to `upload_url`; object lives under `SUPABASE_STORAGE_BUCKET_FF_SAMPLES` "
        "at `storage_path` (`{user_id}/samples/{uuid}`). For data the pipeline cannot process."
    ),
)
def ff_sample_upload_intent(
    user: User = Depends(current_user),
) -> SuccessEnvelope[FfSampleUploadData]:
    settings = get_settings()
    bucket = settings.supabase_storage_bucket_ff_samples
    if not bucket:
        logger.error("SUPABASE_STORAGE_BUCKET_FF_SAMPLES is not set")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="FF samples storage bucket not configured",
        )
    try:
        storage_path, upload_url = create_ff_sample_upload_url(user=user, samples_bucket=bucket)
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e),
        ) from e
    except Exception:
        logger.exception("ff_sample_upload_intent failed")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Could not create sample upload URL",
        ) from None

    return SuccessEnvelope(
        message="Sample upload URL",
        data=FfSampleUploadData(
            upload_url=upload_url,
            storage_path=storage_path,
        ),
    )
