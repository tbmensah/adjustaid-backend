from typing import Any

from fastapi import APIRouter

from app.schemas.envelope import SuccessEnvelope, ok

router = APIRouter(tags=["root"])


@router.get("/")
def read_root() -> SuccessEnvelope[dict[str, str]]:
    return ok({"hello": "world"}, message="Hello")


@router.get("/items/{item_id}")
def read_item(item_id: int, q: str | None = None) -> SuccessEnvelope[dict[str, Any]]:
    return ok({"item_id": item_id, "q": q}, message="Item")
