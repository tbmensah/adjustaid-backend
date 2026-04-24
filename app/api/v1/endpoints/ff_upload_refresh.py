from __future__ import annotations

import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import current_user
from app.core.config import get_settings
from app.db.session import get_db
from app.models.users import User
from app.schemas.envelope import SuccessEnvelope
from app.schemas.ff_draft import FfDraftUploadData
from app.services.ff_upload_refresh import (
    RefreshFfUploadConflict,
    RefreshFfUploadNotFound,
    refresh_ff_upload_url,
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get(
    "/jobs/ff/{job_id}/upload-url",
    summary="New presigned upload URL for same storage path",
    description=(
        "Same object key as draft intent or `pdf_file_key` after details. "
        "Only `draft` or `confirmed` jobs. Use when previous signed URL expired."
    ),
)
def get_ff_upload_url_refresh(
    job_id: uuid.UUID,
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
        jid, storage_path, upload_url = refresh_ff_upload_url(
            db,
            user=user,
            job_id=job_id,
            input_bucket=input_bucket,
        )
    except RefreshFfUploadNotFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="FF job not found",
        ) from None
    except RefreshFfUploadConflict as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=e.detail,
        ) from None
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e),
        ) from e
    except Exception:
        logger.exception("refresh_ff_upload_url failed job_id=%s", job_id)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Could not refresh upload URL",
        ) from None

    return SuccessEnvelope(
        message="OK",
        data=FfDraftUploadData(
            job_id=jid,
            upload_url=upload_url,
            storage_path=storage_path,
        ),
    )
