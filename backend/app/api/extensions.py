from fastapi import APIRouter

from app.services.skill_tool_manager import SkillToolManager

router = APIRouter(prefix="/extensions", tags=["extensions"])


@router.get("")
def list_extensions() -> dict[str, object]:
    return SkillToolManager().list_extensions()
