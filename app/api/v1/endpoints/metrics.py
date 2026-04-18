from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import current_user
from app.db.session import get_db
from app.models.users import User
from app.schemas.envelope import SuccessEnvelope
from app.schemas.metrics import JobStatusSummaryData, UserMetricsData
from app.services.user_metrics import get_job_status_summary, get_user_metrics

router = APIRouter()


@router.get(
    "/metrics",
    summary="Dashboard metrics (tokens + job buckets)",
    description=(
        "Token balances (`ff_balance`, `ee_balance`) plus job counts: `processing` = status processing, "
        "`needs_review` = status failed."
    ),
)
def get_metrics(
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
) -> SuccessEnvelope[UserMetricsData]:
    data = get_user_metrics(db, user=user)
    return SuccessEnvelope(message="OK", data=data)


@router.get(
    "/metrics/job-status-summary",
    summary="Job status counts for dashboard",
    description=(
        "Per-user counts grouped for UI: `draft`; `submitted` = confirmed + queued; `processing`; "
        "`completed`; `failed`. `needs_review` currently matches `failed` (no separate enum yet)."
    ),
)
def get_job_status_summary_endpoint(
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
) -> SuccessEnvelope[JobStatusSummaryData]:
    data = get_job_status_summary(db, user=user)
    return SuccessEnvelope(message="OK", data=data)
