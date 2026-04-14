from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends

from app.api.deps import jwt_payload
from app.schemas.envelope import SuccessEnvelope, ok

router = APIRouter()


@router.get("/me", summary="Protected — validates Supabase access JWT")
def me(payload: dict[str, Any] = Depends(jwt_payload)) -> SuccessEnvelope[dict[str, Any]]:
    """Returns claims if `Authorization: Bearer <access_token>` verifies."""
    return ok(
        {
            "sub": payload.get("sub"),
            "email": payload.get("email"),
            "role": payload.get("role"),
        },
        message="Authenticated",
    )
