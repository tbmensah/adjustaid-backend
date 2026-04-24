"""Back-office job queue: all customers' jobs (requires `user_type=back_office`)."""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import require_back_office
from app.db.session import get_db
from app.models.enums import JobStatus, JobType
from app.models.users import User
from app.schemas.envelope import SuccessEnvelope
from app.schemas.job_history import JobHistoryPage
from app.services.job_history import list_all_jobs_for_ops, search_all_jobs_for_ops

router = APIRouter()


@router.get(
    "/ops/jobs/search",
    summary="[Back office] Search all jobs by project / file name",
    description=(
        "Same filters as `GET /jobs/search` but across **all** customers. "
        "**403** unless `user_type` is `back_office`. Each item includes `owner_id`."
    ),
)
def ops_search_jobs(
    db: Session = Depends(get_db),
    _: User = Depends(require_back_office),
    q: str = Query(
        ...,
        min_length=1,
        max_length=1024,
        description="Substring to match against `original_filename`.",
    ),
    job_type: JobType | None = Query(default=None, description="Optional: only ee or ff."),
    status: list[JobStatus] | None = Query(
        default=None,
        description="Filter by job status (repeat param for multiple). `draft` never returned.",
    ),
    created_from: datetime | None = Query(
        default=None,
        description="Include jobs with created_at >= this instant (timezone-aware ISO 8601).",
    ),
    created_to: datetime | None = Query(
        default=None,
        description="Include jobs with created_at <= this instant.",
    ),
    has_output: bool | None = Query(
        default=None,
        description="If true, only jobs with a non-empty output_file_key (EE or FF). If false, only without.",
    ),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
) -> SuccessEnvelope[JobHistoryPage]:
    items, total = search_all_jobs_for_ops(
        db,
        q=q,
        job_type=job_type,
        status=status,
        created_from=created_from,
        created_to=created_to,
        has_output=has_output,
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
    "/ops/jobs",
    summary="[Back office] List all jobs (paginated)",
    description=(
        "Same filters as `GET /jobs` but across **all** customers. "
        "**403** unless `user_type` is `back_office`. Each item includes `owner_id`."
    ),
)
def ops_list_jobs(
    db: Session = Depends(get_db),
    _: User = Depends(require_back_office),
    job_type: JobType | None = Query(
        default=None,
        description="Restrict to express estimate (ee) or fast fill (ff). Omit for both.",
    ),
    status: list[JobStatus] | None = Query(
        default=None,
        description="Filter by job status (repeat param for multiple). `draft` never returned.",
    ),
    created_from: datetime | None = Query(
        default=None,
        description="Include jobs with created_at >= this instant (timezone-aware ISO 8601).",
    ),
    created_to: datetime | None = Query(
        default=None,
        description="Include jobs with created_at <= this instant.",
    ),
    has_output: bool | None = Query(
        default=None,
        description="If true, only jobs with a non-empty output_file_key (EE or FF). If false, only without.",
    ),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
) -> SuccessEnvelope[JobHistoryPage]:
    items, total = list_all_jobs_for_ops(
        db,
        job_type=job_type,
        status=status,
        created_from=created_from,
        created_to=created_to,
        has_output=has_output,
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
