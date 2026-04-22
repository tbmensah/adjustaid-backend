"""Paginated job history for the authenticated user."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.models.enums import FfPdfType, JobStatus, JobType


class JobHistoryItem(BaseModel):
    id: uuid.UUID
    owner_id: uuid.UUID = Field(
        description="App user id of the job owner. For customers this is always your own id.",
    )
    job_type: JobType
    status: JobStatus
    original_filename: str | None
    created_at: datetime
    updated_at: datetime
    completed_at: datetime | None
    error_message: str | None
    ff_pdf_type: FfPdfType | None = Field(
        default=None,
        description="Set when job_type is ff and details exist.",
    )
    token_cost: int = Field(
        description="Billable units for this row: 1 when job completed (processed file), else 0.",
    )
    download_url: str | None = Field(
        default=None,
        description="Time-limited read URL when `output_file_key` exists and signing succeeds; else null.",
    )


class JobHistoryPage(BaseModel):
    items: list[JobHistoryItem]
    total: int
    page: int = Field(ge=1)
    page_size: int = Field(ge=1, le=100)
