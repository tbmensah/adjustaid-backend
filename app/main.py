from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from app.api.endpoints import root
from app.api.router import api_router
from app.core.config import get_settings
from app.core.exception_handlers import register_exception_handlers

_settings = get_settings()
_openapi_kwargs = (
    {}
    if _settings.is_development
    else {"docs_url": None, "redoc_url": None, "openapi_url": None}
)

app = FastAPI(
    title="AdjustAid API",
    swagger_ui_parameters={
        "persistAuthorization": True,
    },
    **_openapi_kwargs,
)

register_exception_handlers(app)
_cors_origins = [o.strip() for o in _settings.cors_origins.split(",") if o.strip()]
if _cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=_cors_origins,
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )

app.include_router(root.router)
app.include_router(api_router, prefix="/api")
