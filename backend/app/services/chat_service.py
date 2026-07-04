from __future__ import annotations

from typing import Any

from app.services.answer_generator import AnswerGenerator
from app.services.chat_memory import chat_memory
from app.services.intent_router import LLMIntentRouter
from app.services.nl2sql_service import NL2SQLService
from app.services.skill_tool_manager import SkillToolManager


class ChatService:
    def __init__(self) -> None:
        self.router = LLMIntentRouter()
        self.answer_generator = AnswerGenerator()
        self.nl2sql = NL2SQLService()
        self.skill_tools = SkillToolManager()

    def chat(self, message: str, session_id: str | None = None, limit: int = 10) -> dict[str, Any]:
        sid = chat_memory.ensure_session(session_id)
        history = chat_memory.history(sid)
        decision = self.router.route(message, history)
        chat_memory.add(sid, "user", message)

        if decision.route == "general_chat":
            answer = self.answer_generator.general_chat(message, history)
            chat_memory.add(sid, "assistant", answer)
            return {
                "session_id": sid,
                "route": decision.route,
                "answer": answer,
                "question": decision.rewritten_question,
                "history": chat_memory.history(sid),
            }

        result = self.nl2sql.query(decision.rewritten_question, limit=limit)
        extension_result = self.skill_tools.run(
            question=decision.rewritten_question,
            route=decision.route,
            rows=list(result.get("rows", [])),
            columns=list(result.get("columns", [])),
        )
        answer = self.answer_generator.answer(
            route=decision.route,
            question=decision.rewritten_question,
            history=history,
            sql=str(result.get("sql", "")),
            rows=list(result.get("rows", [])),
            tool_results=list(extension_result.get("tool_results", [])),
        )
        chat_memory.add(sid, "assistant", answer)
        return {
            "session_id": sid,
            "route": decision.route,
            "answer": answer,
            "question": decision.rewritten_question,
            "intent": result.get("intent"),
            "sql": result.get("sql"),
            "steps": result.get("steps", []),
            "context": result.get("context", []),
            "columns": result.get("columns", []),
            "rows": result.get("rows", []),
            "matched_skills": extension_result.get("matched_skills", []),
            "tool_results": extension_result.get("tool_results", []),
            "history": chat_memory.history(sid),
        }
