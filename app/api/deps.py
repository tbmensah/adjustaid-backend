"""FastAPI dependencies: Supabase JWT verification."""

from typing import Any

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt.exceptions import InvalidTokenError

from app.core.config import get_settings

bearer_scheme = HTTPBearer(
    bearerFormat="JWT",
    description="`access_token` from Supabase client after sign-in (HS256, same secret as Dashboard JWT Secret).",
    scheme_name="Bearer",
)


def jwt_payload(
    creds: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> dict[str, Any]:
    settings = get_settings()
    secret = settings.supabase_jwt_secret
    if not secret:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="SUPABASE_JWT_SECRET not configured",
        )
    try:
        return jwt.decode(
            creds.credentials,
            secret,
            algorithms=["HS256"],
            options={
                "verify_signature": True,
                "verify_exp": True,
                "verify_aud": False,
            },
        )
    except InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        ) from None
