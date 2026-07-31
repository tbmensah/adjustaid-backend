from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.deps import current_user
from app.models.users import User
from app.schemas.envelope import SuccessEnvelope, ok
from app.schemas.me import MeProfileData

router = APIRouter()


@router.get("/me", summary="Protected — app user profile")
def me(
    user: User = Depends(current_user),
) -> SuccessEnvelope[MeProfileData]:
    """Loads `public.users` for the signed-in user (enforces app-session max age)."""
    return ok(
        MeProfileData(
            id=user.id,
            auth_id=user.auth_id,
            email=user.email,
            full_name=user.full_name,
            company=user.company,
            user_type=user.user_type,
            last_login_at=user.last_login_at,
        ),
        message="Authenticated",
    )
