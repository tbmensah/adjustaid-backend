"""FastAPI dependencies: Supabase JWT verification."""

from __future__ import annotations

import logging
from functools import lru_cache
from typing import Any

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import PyJWKClient
from jwt.exceptions import DecodeError, InvalidTokenError, PyJWKClientConnectionError, PyJWKClientError

from app.core.config import get_settings

logger = logging.getLogger(__name__)

bearer_scheme = HTTPBearer(
    bearerFormat="JWT",
    description="Supabase session `access_token` (ES256/RS256 via JWKS when `SUPABASE_URL` is set; else HS256 + `SUPABASE_JWT_SECRET`).",
    scheme_name="Bearer",
)


@lru_cache(maxsize=8)
def _jwks_client(jwks_url: str) -> PyJWKClient:
    return PyJWKClient(jwks_url, cache_keys=True, cache_jwk_set=True)


def _issuer(settings_url: str) -> str:
    return f"{settings_url.rstrip('/')}/auth/v1"


def _decode_asymmetric(token: str, settings) -> dict[str, Any]:
    base = settings.supabase_url
    if not base:
        logger.error("JWT is asymmetric but SUPABASE_URL is not set")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="SUPABASE_URL not configured (required for ES256/RS256 tokens)",
        )
    jwks_url = f"{base.rstrip('/')}/auth/v1/.well-known/jwks.json"
    iss = _issuer(base)
    try:
        signing_key = _jwks_client(jwks_url).get_signing_key_from_jwt(token)
    except PyJWKClientConnectionError as e:
        logger.exception("JWKS fetch failed: %s", jwks_url)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Could not reach token signing keys",
        ) from e
    except PyJWKClientError as e:
        logger.warning("JWT signing key lookup failed: %s", e)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        ) from None
    alg = jwt.get_unverified_header(token).get("alg")
    try:
        return jwt.decode(
            token,
            signing_key.key,
            algorithms=[alg] if alg else ["ES256", "RS256"],
            audience="authenticated",
            issuer=iss,
            options={
                "verify_signature": True,
                "verify_exp": True,
                "verify_aud": True,
            },
        )
    except InvalidTokenError as e:
        logger.warning("JWT decode failed (asymmetric): %s", e)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        ) from None


def _decode_hs256(token: str, secret: str) -> dict[str, Any]:
    try:
        return jwt.decode(
            token,
            secret,
            algorithms=["HS256"],
            options={
                "verify_signature": True,
                "verify_exp": True,
                "verify_aud": False,
            },
        )
    except InvalidTokenError as e:
        logger.warning("JWT decode failed (HS256): %s", e)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        ) from None


def jwt_payload(
    creds: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> dict[str, Any]:
    settings = get_settings()
    token = creds.credentials
    try:
        header = jwt.get_unverified_header(token)
    except DecodeError as e:
        logger.warning("JWT header decode failed: %s", e)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        ) from None

    alg = header.get("alg")

    if alg in ("ES256", "RS256"):
        return _decode_asymmetric(token, settings)

    if alg == "HS256":
        secret = settings.supabase_jwt_secret
        if not secret:
            logger.error("JWT is HS256 but SUPABASE_JWT_SECRET is not set")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="SUPABASE_JWT_SECRET not configured",
            )
        return _decode_hs256(token, secret)

    logger.warning("Unsupported JWT algorithm: %s", alg)
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=f"Unsupported token algorithm: {alg}",
    )
