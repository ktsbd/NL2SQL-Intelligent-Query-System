from fastapi import APIRouter

from app.services.evaluation_service import EvaluationService
from app.services.task_service import TaskService

router = APIRouter(prefix="/evaluation", tags=["evaluation"])


@router.post("/run")
def run_evaluation() -> dict[str, object]:
    return EvaluationService().run_default()


@router.post("/run-async")
def run_evaluation_async() -> dict[str, object]:
    return TaskService().submit(
        task_type="evaluation.default",
        payload={"name": "default_nl2sql_planner_regression"},
        fn=lambda: EvaluationService().run_default(),
    )
