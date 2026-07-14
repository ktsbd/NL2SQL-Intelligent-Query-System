from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.datasets import router as datasets_router
from app.api.chat import router as chat_router
from app.api.extensions import router as extensions_router
from app.api.evaluation import router as evaluation_router
from app.api.health import router as health_router
from app.api.metadata import router as metadata_router
from app.api.nl2sql import router as nl2sql_router
from app.api.tasks import router as tasks_router
from app.api.traces import router as traces_router
from app.core.config import settings
from app.db.runtime import ensure_runtime_schema
from app.services.task_service import TaskService


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
app.include_router(chat_router, prefix="/api")
app.include_router(extensions_router, prefix="/api")
app.include_router(evaluation_router, prefix="/api")
app.include_router(traces_router, prefix="/api")
app.include_router(tasks_router, prefix="/api")


@app.on_event("startup")
def startup() -> None:
    ensure_runtime_schema()
    TaskService().mark_interrupted_tasks()


@app.get("/")
def root() -> dict[str, str]:
    return {"message": "NL2SQL Intelligent Query System"}
