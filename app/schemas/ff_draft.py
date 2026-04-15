"""Fast Fill draft upload intent response."""

from __future__ import annotations

import uuid

from pydantic import BaseModel


class FfDraftUploadData(BaseModel):
    job_id: uuid.UUID
    upload_url: str
    storage_path: str
