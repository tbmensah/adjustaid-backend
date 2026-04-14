"""Standard API response envelopes."""

from __future__ import annotations

from typing import Any, Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")


class ErrorBody(BaseModel):
    """Structured error payload (machine code + optional details)."""

    model_config = ConfigDict(extra="allow")

    code: str | None = Field(default=None, description="Stable machine-readable code.")
    details: Any = Field(
        default=None,
        description="Extra context: string, validation error list, or object.",
    )


class ErrorEnvelope(BaseModel):
    message: str
    error: ErrorBody


class SuccessEnvelope(BaseModel, Generic[T]):
    message: str = "OK"
    data: T | None = None

    model_config = ConfigDict(arbitrary_types_allowed=True)


def ok(data: Any = None, *, message: str = "OK") -> SuccessEnvelope[Any]:
    """Build success body for route handlers."""
    return SuccessEnvelope(message=message, data=data)
