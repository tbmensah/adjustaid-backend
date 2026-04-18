from __future__ import annotations

import logging
from typing import Annotated

from fastapi import APIRouter, Body, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import current_user
from app.db.session import get_db
from app.models.users import User
from app.schemas.ee_job import EeJobCreatedData
from app.schemas.ee_payload import ExpressEstimatePayload
from app.schemas.envelope import SuccessEnvelope
from app.services.ee_job_create import create_ee_job_from_payload

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/jobs/ee",
    summary="Submit Express Estimate (JSON object → JSONB)",
    description=(
        "Express Estimate wizard JSON (camelCase keys). `projectDetails.projectName` and "
        "`projectDetails.claimNumber` required; other sections optional; unknown keys rejected. "
        "Stored in `job_details_ee.payload` (only keys present in request). Validation errors return 400."
    ),
)
def submit_express_estimate(
    payload: Annotated[
        ExpressEstimatePayload,
        Body(
            openapi_examples={
                "minimal": {
                    "summary": "Required project fields only",
                    "value": {
                        "projectDetails": {
                            "projectName": "Example",
                            "claimNumber": "CLM-001",
                        },
                    },
                },
                "with_sections": {
                    "summary": "Project + optional sections",
                    "value": {
                        "projectDetails": {
                            "projectName": "Example",
                            "claimNumber": "CLM-001",
                            "notes": "Optional note",
                        },
                        "exterior": {
                            "pressureWash": {"enabled": True, "perimeterFeet": "120"},
                        },
                        "rooms": [{"id": 1, "name": "Kitchen"}],
                    },
                },
            },
        ),
    ],
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
) -> SuccessEnvelope[EeJobCreatedData]:
    try:
        stored = payload.model_dump(mode="json", exclude_unset=True, by_alias=True)
        job = create_ee_job_from_payload(db, user=user, payload=stored)
    except Exception:
        logger.exception("submit_express_estimate failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not create EE job",
        ) from None

    return SuccessEnvelope(
        message="OK",
        data=EeJobCreatedData(job_id=job.id, status=job.status),
    )
