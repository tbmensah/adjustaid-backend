from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import current_user_allow_expired_session
from app.core.config import get_settings
from app.db.session import get_db
from app.models.users import User
from app.schemas.envelope import SuccessEnvelope, ok

router = APIRouter()


def _ensure_session_start_allowed(user: User) -> None:
    """429 if the same user stamped session/start too recently."""
    min_interval = get_settings().app_session_start_min_interval_seconds
    if min_interval <= 0:
        return

    login_at = user.last_login_at
    if login_at is None:
        return

    if login_at.tzinfo is None:
        login_at = login_at.replace(tzinfo=timezone.utc)

    elapsed = (datetime.now(timezone.utc) - login_at).total_seconds()
    if elapsed < min_interval:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "code": "session_start_rate_limited",
                "message": "Session start called too soon; try again later",
                "retry_after_seconds": max(1, int(min_interval - elapsed)),
            },
        )


@router.post(
    "/session/start",
    summary="Start or renew app session",
    description=(
        "Stamps `users.last_login_at` for the signed-in Supabase user. "
        "Call after Supabase sign-in (and to renew after `app_session_expired`). "
        "Does not enforce app-session max age. "
        "Rate-limited per user via `APP_SESSION_START_MIN_INTERVAL_SECONDS`."
    ),
)
def start_session(
    user: User = Depends(current_user_allow_expired_session),
    db: Session = Depends(get_db),
) -> SuccessEnvelope[Any]:
    _ensure_session_start_allowed(user)
    user.last_login_at = datetime.now(timezone.utc)
    db.add(user)
    return ok(message="OK")
