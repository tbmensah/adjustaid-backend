from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.models.enums import UserType


class MeProfileData(BaseModel):
    """Public profile for the signed-in app user."""

    id: uuid.UUID
    auth_id: uuid.UUID = Field(description="Matches JWT `sub` (Supabase Auth user id).")
    email: str
    full_name: str
    company: str | None
    user_type: UserType
    last_login_at: datetime | None = Field(
        default=None,
        description="App session stamp from POST /api/v1/session/start.",
    )
