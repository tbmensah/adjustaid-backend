from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import current_user_allow_expired_session
from app.db.session import get_db
from app.models.users import User
from app.schemas.envelope import SuccessEnvelope, ok

router = APIRouter()


@router.post(
    "/session/start",
    summary="Start or renew app session",
    description=(
        "Stamps `users.last_login_at` for the signed-in Supabase user. "
        "Call after Supabase sign-in (and to renew after `app_session_expired`). "
        "Does not enforce app-session max age."
    ),
)
def start_session(
    user: User = Depends(current_user_allow_expired_session),
    db: Session = Depends(get_db),
) -> SuccessEnvelope[Any]:
    user.last_login_at = datetime.now(timezone.utc)
    db.add(user)
    return ok(message="OK")
