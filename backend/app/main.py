from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.datasets import router as datasets_router
from app.api.health import router as health_router
from app.api.metadata import router as metadata_router
from app.api.nl2sql import router as nl2sql_router
from app.core.config import settings


app = FastAPI(title=settings.app_name)

cors_origins = [origin.strip() for origin in settings.cors_origins.split(",") if origin.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router, prefix="/api")
app.include_router(datasets_router, prefix="/api")
app.include_router(metadata_router, prefix="/api")
app.include_router(nl2sql_router, prefix="/api")


@app.get("/")
def root() -> dict[str, str]:
    return {"message": "NL2SQL Intelligent Query System"}
