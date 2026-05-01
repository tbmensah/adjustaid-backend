from __future__ import annotations

import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import current_user
from app.db.session import get_db
from app.models.users import User
from app.schemas.envelope import SuccessEnvelope
from app.schemas.ff_job import FfJobDetailsData, FfJobDetailsRequest
from app.services.ff_job_details import (
    SubmitFfJobDetailsBadRequest,
    SubmitFfJobDetailsConflict,
    SubmitFfJobDetailsNotFound,
    submit_ff_job_details,
)
from app.services.job_token_debit import InsufficientTokensError

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/jobs/ff/{job_id}/details",
    summary="Submit Fast Fill job metadata",
    description=(
        "Requires draft FF job from `GET .../draft-upload`. "
        "Sets `ff_pdf_type`, required `original_filename` (stored on `jobs`), optional storage keys; "
        "creates `job_details_ff` and moves job to `confirmed`. "
        "Charges the **job owner's** FF balance (`FF_JOB_SUBMIT_TOKEN_COST`, default 1); **402** if insufficient."
    ),
)
def submit_ff_job_details_endpoint(
    job_id: uuid.UUID,
    body: FfJobDetailsRequest,
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
) -> SuccessEnvelope[FfJobDetailsData]:
    try:
        job = submit_ff_job_details(db, user=user, job_id=job_id, body=body)
    except InsufficientTokensError as e:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail=str(e),
        ) from e
    except SubmitFfJobDetailsNotFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="FF job not found",
        ) from None
    except SubmitFfJobDetailsBadRequest as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=e.detail,
        ) from None
    except SubmitFfJobDetailsConflict as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=e.detail,
        ) from None
    except Exception:
        logger.exception("submit_ff_job_details failed job_id=%s", job_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not save job details",
        ) from None

    return SuccessEnvelope(
        message="Job details saved",
        data=FfJobDetailsData(job_id=job.id, status=job.status),
    )
