"""Map FastAPI/Starlette exceptions to `ErrorEnvelope`."""

from __future__ import annotations

import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.responses import JSONResponse

from app.schemas.envelope import ErrorBody, ErrorEnvelope

logger = logging.getLogger(__name__)


def _status_default_message(status_code: int) -> str:
    return {
        400: "Bad request",
        401: "Unauthorized",
        403: "Forbidden",
        404: "Not found",
        405: "Method not allowed",
        409: "Conflict",
        422: "Unprocessable entity",
        429: "Too many requests",
        500: "Internal server error",
    }.get(status_code, "Error")


def _http_exception_message(exc: StarletteHTTPException) -> str:
    d = exc.detail
    if isinstance(d, str) and d.strip():
        return d
    return _status_default_message(exc.status_code)


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        _request: Request,
        exc: RequestValidationError,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content=ErrorEnvelope(
                message="Request validation failed",
                error=ErrorBody(code="validation_error", details=exc.errors()),
            ).model_dump(),
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(_request: Request, exc: StarletteHTTPException) -> JSONResponse:
        code = f"http_{exc.status_code}"
        detail = exc.detail
        if isinstance(detail, str):
            err = ErrorBody(code=code, details=None)
        else:
            err = ErrorBody(code=code, details=detail)
        return JSONResponse(
            status_code=exc.status_code,
            content=ErrorEnvelope(
                message=_http_exception_message(exc),
                error=err,
            ).model_dump(),
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(_request: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unhandled error")
        return JSONResponse(
            status_code=500,
            content=ErrorEnvelope(
                message="Internal server error",
                error=ErrorBody(code="internal_error", details=None),
            ).model_dump(),
        )
