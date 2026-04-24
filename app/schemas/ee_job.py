"""Express Estimate (EE) job create response."""

from __future__ import annotations

import uuid

from pydantic import BaseModel

from app.models.enums import JobStatus


class EeJobCreatedData(BaseModel):
    job_id: uuid.UUID
    status: JobStatus
