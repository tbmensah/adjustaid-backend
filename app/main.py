from fastapi import FastAPI

from app.api.endpoints import root
from app.api.router import api_router

app = FastAPI(
    title="AdjustAid API",
    swagger_ui_parameters={
        "persistAuthorization": True,
    },
)

app.include_router(root.router)
app.include_router(api_router, prefix="/api")
