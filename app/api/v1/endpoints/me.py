from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends

from app.api.deps import current_user, jwt_payload
from app.models.users import User
from app.schemas.envelope import SuccessEnvelope, ok
from app.schemas.me import MeProfileData

router = APIRouter()


@router.get("/me", summary="Protected — app user profile + JWT claims")
def me(
    user: User = Depends(current_user),
    payload: dict[str, Any] = Depends(jwt_payload),
) -> SuccessEnvelope[dict[str, Any]]:
    """Loads `public.users` row (includes `user_type`) plus selected JWT claims."""
    profile = MeProfileData(
        id=user.id,
        auth_id=user.auth_id,
        email=user.email,
        full_name=user.full_name,
        company=user.company,
        user_type=user.user_type,
    )
    return ok(
        {
            "profile": profile.model_dump(mode="json"),
            "claims": {
                "sub": payload.get("sub"),
                "email": payload.get("email"),
                "role": payload.get("role"),
            },
        },
        message="Authenticated",
    )
