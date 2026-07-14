from fastapi import APIRouter, HTTPException

from app.services.task_service import TaskService

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.get("/{task_id}")
def get_task(task_id: str) -> dict[str, object]:
    task = TaskService().get(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return task
