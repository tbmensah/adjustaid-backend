"""Express Estimate (EE) job API schemas."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.models.enums import JobStatus


class EeJobCreatedData(BaseModel):
    job_id: uuid.UUID
    status: JobStatus
    input_render_ready: bool = Field(
        default=False,
        description="True only after back office uploaded `payload.md` (`POST .../input-render`). Always false on create.",
    )


class EeJobDetail(BaseModel):
    job_id: uuid.UUID
    status: JobStatus
    completed_at: datetime | None
    created_at: datetime
    updated_at: datetime
    output_ready: bool = Field(description="True when operator uploaded final output (output_file_key set).")
    has_input_render: bool = Field(description="True when payload.md exists in Storage.")
    error_message: str | None = None


class EeJobDownloadData(BaseModel):
    url: str
    expires_in: int = Field(description="Signed URL lifetime in seconds.")


class EeOutputUploadUrlBody(BaseModel):
    filename: str = Field(..., min_length=1, max_length=512, description="Basename with extension, e.g. report.pdf")


class EeOutputUploadUrlData(BaseModel):
    upload_url: str
    object_path: str
    token: str | None = Field(default=None, description="Upload token if returned by Storage API.")


class EeOutputConfirmBody(BaseModel):
    object_path: str = Field(..., min_length=1, max_length=1024)
