from typing import Any, TypedDict

from langgraph.graph import END, START, StateGraph

from app.services.llm_sql_generator import LLMSQLGenerator
from app.services.metadata_retriever import MetadataRetriever
from app.services.nl2sql_generator import NL2SQLGenerator
from app.services.sql_executor import SQLExecutor
from app.services.intent_router import LLMIntentRouter
from app.services.human_gate import HumanApprovalGate


class NL2SQLState(TypedDict, total=False):
    question: str
    limit: int
    context: list[dict[str, Any]]
    intent: str
    sql: str
    params: dict[str, Any]
    columns: list[str]
    rows: list[dict[str, Any]]
    error: str | None
    repair_attempted: bool
    confirmed: bool
    requires_confirmation: bool
    confirmation_reason: str
    steps: list[str]


class NL2SQLWorkflow:
    def __init__(self) -> None:
        self.retriever = MetadataRetriever()
        self.rule_generator = NL2SQLGenerator()
        self.llm_generator = LLMSQLGenerator()
        self.router = LLMIntentRouter()
        self.executor = SQLExecutor()
        self.human_gate = HumanApprovalGate()
        self.graph = self._build_graph()

    def run(self, question: str, limit: int = 10, confirmed: bool = False) -> dict[str, Any]:
        initial_state: NL2SQLState = {
            "question": question,
            "limit": limit,
            "steps": [],
            "error": None,
            "repair_attempted": False,
            "confirmed": confirmed,
            "requires_confirmation": False,
            "confirmation_reason": "",
        }
        return self.graph.invoke(initial_state)

    def _build_graph(self):
        graph = StateGraph(NL2SQLState)
        graph.add_node("parse_intent", self._parse_intent)
        graph.add_node("retrieve_context", self._retrieve_context)
        graph.add_node("generate_sql", self._generate_sql)
        graph.add_node("validate_sql", self._validate_sql)
        graph.add_node("repair_sql", self._repair_sql)
        graph.add_node("execute_sql", self._execute_sql)

        graph.add_edge(START, "parse_intent")
        graph.add_edge("parse_intent", "retrieve_context")
        graph.add_edge("retrieve_context", "generate_sql")
        graph.add_edge("generate_sql", "validate_sql")
        graph.add_conditional_edges(
            "validate_sql",
            self._route_after_validation,
            {"execute": "execute_sql", "repair": "repair_sql", "finish": END},
        )
        graph.add_edge("repair_sql", "validate_sql")
        graph.add_edge("execute_sql", END)
        return graph.compile()

    def _parse_intent(self, state: NL2SQLState) -> NL2SQLState:
        decision = self.router.route(state["question"], history=[])
        question = decision.rewritten_question or state["question"]
        return {
            **state,
            "question": question,
            "intent": decision.route,
            "steps": [*state.get("steps", []), f"route_intent:{decision.route}"],
        }

    def _retrieve_context(self, state: NL2SQLState) -> NL2SQLState:
        context, diagnostics = self.retriever.search_with_diagnostics(state["question"], limit=8)
        step = f"retrieve_context:rounds={diagnostics.get('rounds', 1)}"
        return {**state, "context": context, "retrieval_diagnostics": diagnostics, "steps": [*state.get("steps", []), step]}

    def _generate_sql(self, state: NL2SQLState) -> NL2SQLState:
        generated = self.llm_generator.generate(state["question"], state.get("context", []), state["limit"])
        if generated:
            intent, sql, params = generated
            return {**state, "intent": intent, "sql": sql, "params": params, "steps": [*state.get("steps", []), "generate_sql:llm"]}

        uploaded = self.rule_generator.generate_uploaded(state["question"], state.get("context", []), state["limit"])
        if uploaded:
            intent, sql, params = uploaded
            return {**state, "intent": intent, "sql": sql, "params": params, "steps": [*state.get("steps", []), "generate_sql:rules_uploaded"]}

        intent, sql, params = self.rule_generator.generate(state["question"], limit=state["limit"])
        return {
            **state,
            "intent": intent,
            "sql": sql,
            "params": params,
            "steps": [*state.get("steps", []), "generate_sql:rules_fallback"],
        }

    def _validate_sql(self, state: NL2SQLState) -> NL2SQLState:
        try:
            self.executor.validate(state["sql"])
        except ValueError as exc:
            return {**state, "error": str(exc), "steps": [*state.get("steps", []), "validate_sql"]}
        confirmation = self.human_gate.check(question=state["question"], sql=state["sql"], limit=state["limit"])
        if confirmation.required and not state.get("confirmed"):
            return {
                **state,
                "error": None,
                "requires_confirmation": True,
                "confirmation_reason": confirmation.reason,
                "steps": [*state.get("steps", []), "validate_sql", "human_confirmation_required"],
            }
        return {**state, "error": None, "requires_confirmation": False, "steps": [*state.get("steps", []), "validate_sql"]}

    def _repair_sql(self, state: NL2SQLState) -> NL2SQLState:
        repaired_sql = self.executor.repair(state["sql"], default_limit=state["limit"])
        return {**state, "sql": repaired_sql, "error": None, "repair_attempted": True, "steps": [*state.get("steps", []), "repair_sql"]}

    def _execute_sql(self, state: NL2SQLState) -> NL2SQLState:
        columns, rows = self.executor.execute(state["sql"], state.get("params", {}))
        return {**state, "columns": columns, "rows": rows, "steps": [*state.get("steps", []), "execute_sql"]}

    def _route_after_validation(self, state: NL2SQLState) -> str:
        if not state.get("error"):
            if state.get("requires_confirmation"):
                return "finish"
            return "execute"
        if not state.get("repair_attempted"):
            return "repair"
        return "finish"
