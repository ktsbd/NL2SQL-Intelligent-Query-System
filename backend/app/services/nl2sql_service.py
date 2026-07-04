from app.services.nl2sql_workflow import NL2SQLWorkflow


class NL2SQLService:
    def __init__(self) -> None:
        self.workflow = NL2SQLWorkflow()

    def query(self, question: str, limit: int = 10) -> dict[str, object]:
        state = self.workflow.run(question, limit=limit)
        if state.get("error"):
            raise ValueError(str(state["error"]))
        return {
            "question": state.get("question", question),
            "intent": state["intent"],
            "sql": state["sql"],
            "steps": state.get("steps", []),
            "context": [self._context_item(item) for item in state.get("context", [])],
            "columns": state.get("columns", []),
            "rows": state.get("rows", []),
        }

    def _context_item(self, item: dict[str, object]) -> dict[str, object]:
        return {
            "object_name": item["object_name"],
            "business_name": item["business_name"],
            "description": item["description"],
            "rank_score": item["rank_score"],
            "sources": item["sources"],
        }
