from __future__ import annotations

from typing import Any

from app.services.answer_generator import AnswerGenerator
from app.services.analysis_planner import AnalysisPlanner
from app.services.chat_memory import chat_memory
from app.services.intent_router import LLMIntentRouter
from app.services.nl2sql_service import NL2SQLService
from app.services.skill_tool_manager import SkillToolManager
from app.services.trace_logger import TraceLogger


class ChatService:
    def __init__(self) -> None:
        self.router = LLMIntentRouter()
        self.answer_generator = AnswerGenerator()
        self.nl2sql = NL2SQLService()
        self.skill_tools = SkillToolManager()
        self.planner = AnalysisPlanner()

    def chat(self, message: str, session_id: str | None = None, limit: int = 10, confirmed: bool = False) -> dict[str, Any]:
        sid = chat_memory.ensure_session(session_id)
        trace = TraceLogger(question=message, session_id=sid)
        history = chat_memory.history(sid)
        decision = self.router.route(message, history)
        try:
            trace.event(
                node_name="route_intent",
                input_data={"message": message, "history_count": len(history)},
                output_data={"route": decision.route, "rewritten_question": decision.rewritten_question, "reason": decision.reason},
            )
            chat_memory.add(sid, "user", message)

            if decision.route == "general_chat":
                answer = self.answer_generator.general_chat(message, history)
                chat_memory.add(sid, "assistant", answer)
                response = {
                    "trace_id": trace.trace_id,
                    "session_id": sid,
                    "route": decision.route,
                    "answer": answer,
                    "question": decision.rewritten_question,
                    "history": chat_memory.history(sid),
                }
                trace.finish(
                    status="success",
                    route=decision.route,
                    rewritten_question=decision.rewritten_question,
                    steps=["route_intent", "answer"],
                )
                return response

            plan = self.planner.plan(decision.rewritten_question, decision.route)
            if plan.enabled:
                trace.event(
                    node_name="planner",
                    input_data={"question": decision.rewritten_question, "route": decision.route},
                    output_data={"reason": plan.reason, "source": plan.source, "tasks": [task.__dict__ for task in plan.tasks]},
                )
                return self._run_plan(
                    trace=trace,
                    sid=sid,
                    decision=decision,
                    history=history,
                    plan=plan,
                    limit=limit,
                    confirmed=confirmed,
                )

            result = self.nl2sql.query(decision.rewritten_question, limit=limit, confirmed=confirmed)
            if result.get("requires_confirmation"):
                answer = f"这个操作需要你确认后再执行：{result.get('confirmation_reason')}"
                chat_memory.add(sid, "assistant", answer)
                response = {
                    "trace_id": trace.trace_id,
                    "session_id": sid,
                    "route": decision.route,
                    "answer": answer,
                    "question": decision.rewritten_question,
                    "intent": result.get("intent"),
                    "sql": result.get("sql"),
                    "steps": result.get("steps", []),
                    "context": result.get("context", []),
                    "columns": [],
                    "rows": [],
                    "requires_confirmation": True,
                    "confirmation_reason": result.get("confirmation_reason"),
                    "matched_skills": [],
                    "tool_results": [],
                    "history": chat_memory.history(sid),
                }
                trace.finish(
                    status="waiting_confirmation",
                    route=decision.route,
                    rewritten_question=decision.rewritten_question,
                    steps=list(result.get("steps", [])),
                    sql=str(result.get("sql", "")),
                    context=list(result.get("context", [])),
                )
                return response

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
            response = {
                "trace_id": trace.trace_id,
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
                "requires_confirmation": False,
                "confirmation_reason": None,
                "matched_skills": extension_result.get("matched_skills", []),
                "tool_results": extension_result.get("tool_results", []),
                "history": chat_memory.history(sid),
            }
            trace.finish(
                status="success",
                route=decision.route,
                rewritten_question=decision.rewritten_question,
                steps=list(result.get("steps", [])),
                sql=str(result.get("sql", "")),
                context=list(result.get("context", [])),
                tool_results=list(extension_result.get("tool_results", [])),
            )
            return response
        except Exception as exc:
            trace.finish(
                status="error",
                route=getattr(decision, "route", ""),
                rewritten_question=getattr(decision, "rewritten_question", message),
                error_message=str(exc),
            )
            raise

    def _run_plan(
        self,
        *,
        trace: TraceLogger,
        sid: str,
        decision,
        history: list[dict[str, str]],
        plan,
        limit: int,
        confirmed: bool,
    ) -> dict[str, Any]:
        plan_results: list[dict[str, Any]] = []
        combined_steps = ["route_intent", "planner"]
        combined_sql = []
        combined_context: list[dict[str, object]] = []
        for task in plan.tasks:
            result = self._execute_plan_task(trace=trace, task=task, limit=limit, confirmed=confirmed)
            if result.get("requires_confirmation"):
                answer = f"这个多步骤分析需要你确认后再执行：{result.get('confirmation_reason')}"
                chat_memory.add(sid, "assistant", answer)
                response = {
                    "trace_id": trace.trace_id,
                    "session_id": sid,
                    "route": decision.route,
                    "answer": answer,
                    "question": decision.rewritten_question,
                    "intent": result.get("intent"),
                    "sql": result.get("sql"),
                    "steps": [*combined_steps, *list(result.get("steps", [])), "human_confirmation_required"],
                    "context": result.get("context", []),
                    "columns": [],
                    "rows": [],
                    "requires_confirmation": True,
                    "confirmation_reason": result.get("confirmation_reason"),
                    "matched_skills": [],
                    "tool_results": [],
                    "plan_results": plan_results,
                    "history": chat_memory.history(sid),
                }
                trace.finish(
                    status="waiting_confirmation",
                    route=decision.route,
                    rewritten_question=decision.rewritten_question,
                    steps=response["steps"],
                    sql=str(result.get("sql", "")),
                    context=list(result.get("context", [])),
                )
                return response

            if not result.get("rows"):
                replan_task = self.planner.replan_empty_task(decision.rewritten_question, task)
                if replan_task is not None:
                    trace.event(
                        node_name="replan",
                        input_data={"failed_task": task.__dict__, "reason": "empty_rows"},
                        output_data={"task": replan_task.__dict__},
                    )
                    retry_result = self._execute_plan_task(trace=trace, task=replan_task, limit=limit, confirmed=confirmed)
                    if not retry_result.get("requires_confirmation"):
                        result = retry_result
                        task = replan_task

            with trace.span("planner_skill_tools", input_data={"task": task.name, "columns": result.get("columns", [])}):
                extension_result = self.skill_tools.run(
                    question=task.question,
                    route=decision.route,
                    rows=list(result.get("rows", [])),
                    columns=list(result.get("columns", [])),
                )
            task_result = {
                "name": task.name,
                "goal": task.goal,
                "question": task.question,
                "intent": result.get("intent"),
                "sql": result.get("sql"),
                "steps": result.get("steps", []),
                "columns": result.get("columns", []),
                "rows": result.get("rows", []),
                "matched_skills": extension_result.get("matched_skills", []),
                "tool_results": extension_result.get("tool_results", []),
            }
            trace.event(
                node_name="planner_task_result",
                input_data={"name": task.name},
                output_data={
                    "intent": result.get("intent"),
                    "rows": len(result.get("rows", [])),
                    "tools": [item.get("name") for item in extension_result.get("tool_results", [])],
                },
            )
            plan_results.append(task_result)
            combined_steps.extend(list(result.get("steps", [])))
            if result.get("sql"):
                combined_sql.append(f"-- {task.name}\n{result['sql']}")
            combined_context.extend(list(result.get("context", [])))

        answer = self.answer_generator.answer_plan(
            question=decision.rewritten_question,
            history=history,
            plan_results=plan_results,
        )
        chat_memory.add(sid, "assistant", answer)
        first_result = plan_results[0] if plan_results else {}
        all_tool_results = [tool for item in plan_results for tool in item.get("tool_results", [])]
        response = {
            "trace_id": trace.trace_id,
            "session_id": sid,
            "route": decision.route,
            "answer": answer,
            "question": decision.rewritten_question,
            "intent": "multi_step_analysis",
            "sql": "\n\n".join(combined_sql),
            "steps": combined_steps,
            "context": combined_context[:12],
            "columns": first_result.get("columns", []),
            "rows": first_result.get("rows", []),
            "requires_confirmation": False,
            "confirmation_reason": None,
            "matched_skills": [skill for item in plan_results for skill in item.get("matched_skills", [])],
            "tool_results": all_tool_results,
            "plan_results": plan_results,
            "history": chat_memory.history(sid),
        }
        trace.finish(
            status="success",
            route=decision.route,
            rewritten_question=decision.rewritten_question,
            steps=combined_steps,
            sql=response["sql"],
            context=combined_context[:12],
            tool_results=all_tool_results,
        )
        return response

    def _execute_plan_task(self, *, trace: TraceLogger, task, limit: int, confirmed: bool) -> dict[str, Any]:
        with trace.span(
            "planner_task",
            input_data={"name": task.name, "question": task.question, "goal": task.goal, "source": task.source},
        ):
            return self.nl2sql.query(task.question, limit=limit, confirmed=confirmed)
