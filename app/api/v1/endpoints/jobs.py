from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import current_user
from app.db.session import get_db
from app.models.enums import JobStatus, JobType
from app.models.users import User
from app.schemas.envelope import SuccessEnvelope
from app.schemas.job_history import JobHistoryPage
from app.services.job_history import list_user_jobs, search_user_jobs_by_id

router = APIRouter()


@router.get(
    "/jobs/search",
    summary="Search jobs by job id substring",
    description=(
        "Case-insensitive substring match on UUID string (hyphens included). "
        "Example: `q=3fa85f64` or full id. Scoped to the signed-in user."
    ),
)
def search_jobs(
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
    q: str = Query(
        ...,
        min_length=1,
        max_length=64,
        description="Fragment of job UUID to match.",
    ),
    job_type: JobType | None = Query(
        default=None,
        description="Optional: only ee or ff.",
    ),
    status: list[JobStatus] | None = Query(
        default=None,
        description="Filter by job status (repeat param for multiple). Omit for any status.",
    ),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
) -> SuccessEnvelope[JobHistoryPage]:
    items, total = search_user_jobs_by_id(
        db,
        user=user,
        q=q,
        job_type=job_type,
        status=status,
        page=page,
        page_size=page_size,
    )
    return SuccessEnvelope(
        message="OK",
        data=JobHistoryPage(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
        ),
    )


@router.get(
    "/jobs",
    summary="Job history (EE + FF)",
    description=(
        "Paginated list for the signed-in user. Filter by `job_type` (ee | ff), `status`, "
        "`created_from` / `created_to` (ISO 8601). Each item includes `status`. "
        "`token_cost` is 1 when status is completed, else 0."
    ),
)
def get_job_history(
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
    job_type: JobType | None = Query(
        default=None,
        description="Restrict to express estimate (ee) or fast fill (ff). Omit for both.",
    ),
    status: list[JobStatus] | None = Query(
        default=None,
        description="Filter by job status (repeat param for multiple). Omit for any status.",
    ),
    created_from: datetime | None = Query(
        default=None,
        description="Include jobs with created_at >= this instant (timezone-aware ISO 8601).",
    ),
    created_to: datetime | None = Query(
        default=None,
        description="Include jobs with created_at <= this instant.",
    ),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
) -> SuccessEnvelope[JobHistoryPage]:
    items, total = list_user_jobs(
        db,
        user=user,
        job_type=job_type,
        status=status,
        created_from=created_from,
        created_to=created_to,
        page=page,
        page_size=page_size,
    )
    return SuccessEnvelope(
        message="OK",
        data=JobHistoryPage(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
        ),
    )
