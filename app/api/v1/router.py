from fastapi import APIRouter

from app.api.v1.endpoints import (
    ee_jobs,
    ff_details,
    ff_draft,
    ff_samples,
    ff_upload_refresh,
    health,
    jobs,
    me,
    metrics,
    ops_jobs,
    tokens,
)

router = APIRouter()
router.include_router(health.router, tags=["health"])
router.include_router(me.router, tags=["auth"])
router.include_router(metrics.router, tags=["metrics"])
router.include_router(tokens.router, tags=["tokens"])
router.include_router(jobs.router, tags=["jobs"])
router.include_router(ops_jobs.router, tags=["jobs", "operations"])
router.include_router(ee_jobs.router, tags=["jobs"])
router.include_router(ff_draft.router, tags=["jobs"])
router.include_router(ff_samples.router, tags=["jobs"])
router.include_router(ff_details.router, tags=["jobs"])
router.include_router(ff_upload_refresh.router, tags=["jobs"])
