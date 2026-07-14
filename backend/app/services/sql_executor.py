from datetime import date, datetime
from decimal import Decimal
import re

from sqlalchemy import text

from app.db.session import engine

FORBIDDEN_SQL = re.compile(
    r"\b(insert|update|delete|drop|alter|truncate|create|replace|grant|revoke|call|exec|merge|use|describe|show)\b",
    re.IGNORECASE,
)
ALLOWED_TABLES = {"stocks", "daily_market", "financial_statements", "factor_values", "business_metrics"}
LIMIT_PATTERN = re.compile(r"\blimit\b", re.IGNORECASE)
LIMIT_VALUE_PATTERN = re.compile(r"\blimit\s+(?P<limit>\d+)", re.IGNORECASE)
SQL_COMMENT_PATTERN = re.compile(r"(--|#|/\*)")
FORBIDDEN_CLAUSE = re.compile(r"\b(union|into\s+outfile|load_file|information_schema|mysql\.|performance_schema|sys\.)\b", re.IGNORECASE)
MAX_LIMIT = 100


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
        if SQL_COMMENT_PATTERN.search(normalized):
            raise SQLValidationError("SQL comments are not allowed.")
        if FORBIDDEN_SQL.search(normalized):
            raise SQLValidationError("Unsafe SQL keyword detected.")
        if FORBIDDEN_CLAUSE.search(normalized):
            raise SQLValidationError("Unsafe SQL clause detected.")
        referenced_tables = set(re.findall(r"\b(?:from|join)\s+([a-zA-Z_][a-zA-Z0-9_]*)", lowered))
        unknown_tables = {table for table in referenced_tables - ALLOWED_TABLES if not table.startswith("uploaded_")}
        if unknown_tables:
            raise SQLValidationError(f"Unknown table detected: {', '.join(sorted(unknown_tables))}.")
        if not LIMIT_PATTERN.search(normalized):
            raise SQLValidationError("SELECT statements must include LIMIT.")
        limit_match = LIMIT_VALUE_PATTERN.search(normalized)
        if limit_match and int(limit_match.group("limit")) > MAX_LIMIT:
            raise SQLValidationError(f"LIMIT must not exceed {MAX_LIMIT}.")

    def repair(self, sql: str, default_limit: int = 10) -> str:
        normalized = self.normalize(sql)
        normalized = re.sub(r";+$", "", normalized.strip())
        if normalized.lower().startswith("select") and not LIMIT_PATTERN.search(normalized):
            normalized = f"{normalized}\nLIMIT {min(int(default_limit), MAX_LIMIT)}"
        match = LIMIT_VALUE_PATTERN.search(normalized)
        if match and int(match.group("limit")) > MAX_LIMIT:
            normalized = LIMIT_VALUE_PATTERN.sub(f"LIMIT {MAX_LIMIT}", normalized, count=1)
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
