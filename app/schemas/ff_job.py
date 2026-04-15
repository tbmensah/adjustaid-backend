"""Fast Fill job detail submission."""

from __future__ import annotations

import uuid

from pydantic import BaseModel, Field

from app.models.enums import FfPdfType, JobStatus


class FfJobDetailsRequest(BaseModel):
    """Metadata after input file upload (PDF type, optional storage keys)."""

    ff_pdf_type: FfPdfType
    pdf_file_key: str | None = Field(
        default=None,
        description="Object path in the input bucket. Defaults to `{user_id}/{job_id}` from draft intent.",
    )
    esx_file_key: str | None = Field(
        default=None,
        description="Optional ESX / secondary input object path in the input bucket.",
    )


class FfJobDetailsData(BaseModel):
    job_id: uuid.UUID
    status: JobStatus
