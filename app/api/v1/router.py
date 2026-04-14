from fastapi import APIRouter

from app.api.v1.endpoints import health, me

router = APIRouter()
router.include_router(health.router, tags=["health"])
router.include_router(me.router, tags=["auth"])
