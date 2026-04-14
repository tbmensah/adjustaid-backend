from fastapi import APIRouter

from app.schemas.envelope import SuccessEnvelope, ok

router = APIRouter()


@router.get("/health")
def health() -> SuccessEnvelope[dict[str, str]]:
    return ok({"status": "ok"}, message="Healthy")
