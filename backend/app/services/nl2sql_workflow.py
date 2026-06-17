from typing import Any, TypedDict

from langgraph.graph import END, START, StateGraph

from app.services.llm_sql_generator import LLMSQLGenerator
from app.services.metadata_retriever import MetadataRetriever
from app.services.nl2sql_generator import NL2SQLGenerator
from app.services.sql_executor import SQLExecutor


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
    steps: list[str]


class NL2SQLWorkflow:
    def __init__(self) -> None:
        self.retriever = MetadataRetriever()
        self.rule_generator = NL2SQLGenerator()
        self.llm_generator = LLMSQLGenerator()
        self.executor = SQLExecutor()
        self.graph = self._build_graph()

    def run(self, question: str, limit: int = 10) -> dict[str, Any]:
        initial_state: NL2SQLState = {
            "question": question,
            "limit": limit,
            "steps": [],
            "error": None,
            "repair_attempted": False,
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
        intent, sql, params = self.rule_generator.generate(state["question"], limit=state["limit"])
        return {**state, "intent": intent, "sql": sql, "params": params, "steps": [*state.get("steps", []), "parse_intent"]}

    def _retrieve_context(self, state: NL2SQLState) -> NL2SQLState:
        context = self.retriever.search(state["question"], limit=8)
        return {**state, "context": context, "steps": [*state.get("steps", []), "retrieve_context"]}

    def _generate_sql(self, state: NL2SQLState) -> NL2SQLState:
        uploaded = self.rule_generator.generate_uploaded(state["question"], state.get("context", []), state["limit"])
        if uploaded:
            intent, sql, params = uploaded
            return {**state, "intent": intent, "sql": sql, "params": params, "steps": [*state.get("steps", []), "generate_sql:uploaded"]}

        generated = self.llm_generator.generate(state["question"], state.get("context", []), state["limit"])
        if generated:
            intent, sql, params = generated
            return {**state, "intent": intent, "sql": sql, "params": params, "steps": [*state.get("steps", []), "generate_sql:llm"]}
        return {**state, "steps": [*state.get("steps", []), "generate_sql:rules"]}

    def _validate_sql(self, state: NL2SQLState) -> NL2SQLState:
        try:
            self.executor.validate(state["sql"])
        except ValueError as exc:
            return {**state, "error": str(exc), "steps": [*state.get("steps", []), "validate_sql"]}
        return {**state, "error": None, "steps": [*state.get("steps", []), "validate_sql"]}

    def _repair_sql(self, state: NL2SQLState) -> NL2SQLState:
        repaired_sql = self.executor.repair(state["sql"], default_limit=state["limit"])
        return {**state, "sql": repaired_sql, "error": None, "repair_attempted": True, "steps": [*state.get("steps", []), "repair_sql"]}

    def _execute_sql(self, state: NL2SQLState) -> NL2SQLState:
        columns, rows = self.executor.execute(state["sql"], state.get("params", {}))
        return {**state, "columns": columns, "rows": rows, "steps": [*state.get("steps", []), "execute_sql"]}

    def _route_after_validation(self, state: NL2SQLState) -> str:
        if not state.get("error"):
            return "execute"
        if not state.get("repair_attempted"):
            return "repair"
        return "finish"
