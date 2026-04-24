"""Aggregate dashboard metrics for one user."""

from __future__ import annotations

from sqlalchemy import and_, func, select
from sqlalchemy.orm import Session

from app.models.billing import TokenWallet
from app.models.enums import JobStatus
from app.models.jobs import Job
from app.models.users import User
from app.schemas.metrics import JobStatusSummaryData, UserMetricsData


def get_user_metrics(db: Session, *, user: User) -> UserMetricsData:
    wallet = db.scalar(select(TokenWallet).where(TokenWallet.user_id == user.id))
    ff_available = int(wallet.ff_balance) if wallet is not None else 0
    ee_available = int(wallet.ee_balance) if wallet is not None else 0

    processing_count = int(
        db.scalar(
            select(func.count())
            .select_from(Job)
            .where(Job.user_id == user.id, Job.status == JobStatus.PROCESSING)
        )
        or 0
    )
    failed_count = int(
        db.scalar(
            select(func.count())
            .select_from(Job)
            .where(Job.user_id == user.id, Job.status == JobStatus.FAILED)
        )
        or 0
    )

    return UserMetricsData(
        fast_fill_tokens=ff_available,
        express_estimate_tokens=ee_available,
        processing=processing_count,
        needs_review=failed_count,
    )


def get_job_status_summary(db: Session, *, user: User) -> JobStatusSummaryData:
    rows = db.execute(
        select(Job.status, func.count())
        .where(Job.user_id == user.id, Job.status != JobStatus.DRAFT)
        .group_by(Job.status)
    ).all()
    counts: dict[JobStatus, int] = {status: int(n) for status, n in rows}

    def n(status: JobStatus) -> int:
        return counts.get(status, 0)

    confirmed = n(JobStatus.CONFIRMED)
    queued = n(JobStatus.QUEUED)
    failed_n = n(JobStatus.FAILED)

    return JobStatusSummaryData(
        draft=n(JobStatus.DRAFT),
        submitted=confirmed + queued,
        processing=n(JobStatus.PROCESSING),
        completed=n(JobStatus.COMPLETED),
        failed=failed_n,
        needs_review=failed_n,
    )
