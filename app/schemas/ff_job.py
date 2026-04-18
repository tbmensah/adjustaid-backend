"""Fast Fill job detail submission."""

from __future__ import annotations

import uuid

from pydantic import BaseModel, Field, field_validator

from app.models.enums import FfPdfType, JobStatus


class FfJobDetailsRequest(BaseModel):
    """Metadata after input file upload (PDF type, optional storage keys)."""

    ff_pdf_type: FfPdfType
    original_filename: str = Field(
        min_length=1,
        max_length=1024,
        description="Client-side PDF file name (stored on `jobs.original_filename`).",
    )
    pdf_file_key: str | None = Field(
        default=None,
        description="Object path in the input bucket. Defaults to `{user_id}/{job_id}` from draft intent.",
    )
    esx_file_key: str | None = Field(
        default=None,
        description="Optional ESX / secondary input object path in the input bucket.",
    )

    @field_validator("original_filename", mode="before")
    @classmethod
    def _strip_original_filename(cls, v: object) -> object:
        if isinstance(v, str):
            return v.strip()
        return v


class FfJobDetailsData(BaseModel):
    job_id: uuid.UUID
    status: JobStatus
