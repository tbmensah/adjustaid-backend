"""Presigned upload for FF sample files (not processed as normal jobs)."""

from __future__ import annotations

from pydantic import BaseModel, Field


class FfSampleUploadData(BaseModel):
    upload_url: str = Field(description="PUT upload URL (time-limited).")
    storage_path: str = Field(description="Object key under the samples bucket; `{user_id}/samples/{uuid}`.")
