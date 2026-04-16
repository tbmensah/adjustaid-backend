from fastapi import APIRouter

from app.api.v1.endpoints import ff_details, ff_draft, ff_upload_refresh, health, jobs, me

router = APIRouter()
router.include_router(health.router, tags=["health"])
router.include_router(me.router, tags=["auth"])
router.include_router(jobs.router, tags=["jobs"])
router.include_router(ff_draft.router, tags=["jobs"])
router.include_router(ff_details.router, tags=["jobs"])
router.include_router(ff_upload_refresh.router, tags=["jobs"])
