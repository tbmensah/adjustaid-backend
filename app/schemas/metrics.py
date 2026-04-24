"""Dashboard metrics for signed-in user."""

from __future__ import annotations

from pydantic import BaseModel, Field


class UserMetricsData(BaseModel):
    fast_fill_tokens: int = Field(ge=0, description="FF token balance.")
    express_estimate_tokens: int = Field(ge=0, description="EE token balance.")
    processing: int = Field(ge=0, description="Jobs in `processing` status.")
    needs_review: int = Field(ge=0, description="Jobs in `failed` status.")


class JobStatusSummaryData(BaseModel):
    """Counts for the signed-in user; `submitted` = confirmed + queued."""

    draft: int = Field(
        ge=0,
        description="Always 0: draft jobs excluded from this summary (same scope as GET /jobs).",
    )
    submitted: int = Field(ge=0, description="Jobs with status `confirmed` or `queued`.")
    processing: int = Field(ge=0)
    completed: int = Field(ge=0)
    failed: int = Field(ge=0)
    needs_review: int = Field(
        ge=0,
        description="Same as `failed` until a distinct status exists in the DB.",
    )
