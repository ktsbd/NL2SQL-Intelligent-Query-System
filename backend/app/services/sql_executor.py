from datetime import date, datetime
from decimal import Decimal
import re

from sqlalchemy import text

from app.db.session import engine

FORBIDDEN_SQL = re.compile(
    r"\b(insert|update|delete|drop|alter|truncate|create|replace|grant|revoke|call|exec)\b",
    re.IGNORECASE,
)
ALLOWED_TABLES = {"stocks", "daily_market", "financial_statements", "factor_values", "business_metrics"}
LIMIT_PATTERN = re.compile(r"\blimit\b", re.IGNORECASE)


class SQLValidationError(ValueError):
    pass


class SQLExecutor:
    def execute(self, sql: str, params: dict[str, object] | None = None) -> tuple[list[str], list[dict[str, object]]]:
        self.validate(sql)
        with engine.connect() as connection:
            result = connection.execute(text(sql), params or {})
            columns = list(result.keys())
            rows = [self._serialize_row(dict(row._mapping)) for row in result]
            return columns, rows

    def validate(self, sql: str) -> None:
        normalized = self.normalize(sql)
        lowered = normalized.lower()
        if not lowered.startswith("select"):
            raise SQLValidationError("Only SELECT statements are allowed.")
        if ";" in normalized:
            raise SQLValidationError("Multiple SQL statements are not allowed.")
        if FORBIDDEN_SQL.search(normalized):
            raise SQLValidationError("Unsafe SQL keyword detected.")
        referenced_tables = set(re.findall(r"\b(?:from|join)\s+([a-zA-Z_][a-zA-Z0-9_]*)", lowered))
        unknown_tables = {table for table in referenced_tables - ALLOWED_TABLES if not table.startswith("uploaded_")}
        if unknown_tables:
            raise SQLValidationError(f"Unknown table detected: {', '.join(sorted(unknown_tables))}.")
        if not LIMIT_PATTERN.search(normalized):
            raise SQLValidationError("SELECT statements must include LIMIT.")

    def repair(self, sql: str, default_limit: int = 10) -> str:
        normalized = self.normalize(sql)
        normalized = re.sub(r";+$", "", normalized.strip())
        if normalized.lower().startswith("select") and not LIMIT_PATTERN.search(normalized):
            normalized = f"{normalized}\nLIMIT {int(default_limit)}"
        return normalized

    def normalize(self, sql: str) -> str:
        return sql.strip().rstrip(";")

    def _serialize_row(self, row: dict[str, object]) -> dict[str, object]:
        serialized = {}
        for key, value in row.items():
            if isinstance(value, Decimal):
                serialized[key] = float(value)
            elif isinstance(value, (date, datetime)):
                serialized[key] = value.isoformat()
            else:
                serialized[key] = value
        return serialized
