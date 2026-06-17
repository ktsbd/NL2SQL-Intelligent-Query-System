from __future__ import annotations

import csv
import io
import re
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal, InvalidOperation

from sqlalchemy import text

from app.db.models import MetadataCatalog
from app.db.session import SessionLocal, engine
from app.services.metadata_indexer import MetadataIndexer


MAX_ROWS = 20000
IDENTIFIER_RE = re.compile(r"[^a-zA-Z0-9_]+")
DATE_PATTERNS = ("%Y-%m-%d", "%Y/%m/%d", "%Y%m%d", "%Y-%m-%d %H:%M:%S", "%Y/%m/%d %H:%M:%S")


@dataclass(frozen=True)
class ColumnSpec:
    original_name: str
    sql_name: str
    mysql_type: str


class CSVDatasetImporter:
    def import_csv(self, file_bytes: bytes, filename: str, dataset_name: str | None = None) -> dict[str, object]:
        decoded = self._decode(file_bytes)
        reader = csv.DictReader(io.StringIO(decoded))
        if not reader.fieldnames:
            raise ValueError("CSV 文件缺少表头。")

        rows = [row for index, row in enumerate(reader) if index < MAX_ROWS]
        if not rows:
            raise ValueError("CSV 文件没有可导入的数据行。")

        display_name = (dataset_name or filename.rsplit(".", 1)[0]).strip()
        table_name = self._table_name(display_name)
        columns = self._build_columns(reader.fieldnames, rows)

        self._create_table(table_name, columns)
        inserted = self._insert_rows(table_name, columns, rows)
        self._upsert_metadata(table_name, display_name, filename, columns, rows, inserted)
        indexed = MetadataIndexer().rebuild()["indexed"]

        return {
            "table_name": table_name,
            "dataset_name": display_name,
            "columns": [{"original_name": col.original_name, "sql_name": col.sql_name, "mysql_type": col.mysql_type} for col in columns],
            "rows_inserted": inserted,
            "indexed": indexed,
        }

    def _decode(self, file_bytes: bytes) -> str:
        for encoding in ("utf-8-sig", "utf-8", "gb18030", "gbk"):
            try:
                return file_bytes.decode(encoding)
            except UnicodeDecodeError:
                continue
        raise ValueError("无法识别 CSV 文件编码，请使用 UTF-8 或 GBK 编码。")

    def _table_name(self, dataset_name: str) -> str:
        cleaned = IDENTIFIER_RE.sub("_", dataset_name).strip("_").lower()
        if not cleaned:
            cleaned = "dataset"
        if not cleaned[0].isalpha():
            cleaned = f"dataset_{cleaned}"
        base_name = f"uploaded_{cleaned[:40]}"
        with engine.connect() as connection:
            existing = {
                row[0]
                for row in connection.execute(
                    text("SELECT table_name FROM information_schema.tables WHERE table_schema = DATABASE() AND table_name LIKE 'uploaded_%'")
                )
            }
        if base_name not in existing:
            return base_name
        suffix = datetime.now().strftime("%Y%m%d%H%M%S")
        return f"{base_name[:45]}_{suffix}"

    def _build_columns(self, headers: list[str], rows: list[dict[str, str]]) -> list[ColumnSpec]:
        used_names = {"id"}
        columns = []
        for index, header in enumerate(headers, start=1):
            original_name = (header or f"column_{index}").strip()
            sql_name = self._column_name(original_name, index, used_names)
            sample_values = [row.get(header, "") for row in rows[:200]]
            columns.append(ColumnSpec(original_name=original_name, sql_name=sql_name, mysql_type=self._infer_type(sample_values)))
        return columns

    def _column_name(self, original_name: str, index: int, used_names: set[str]) -> str:
        cleaned = IDENTIFIER_RE.sub("_", original_name).strip("_").lower()
        if not cleaned:
            cleaned = f"column_{index}"
        if not cleaned[0].isalpha():
            cleaned = f"c_{cleaned}"
        candidate = cleaned[:54]
        counter = 2
        while candidate in used_names:
            candidate = f"{cleaned[:49]}_{counter}"
            counter += 1
        used_names.add(candidate)
        return candidate

    def _infer_type(self, values: list[str]) -> str:
        non_empty = [str(value).strip() for value in values if str(value).strip()]
        if not non_empty:
            return "TEXT"
        if all(self._is_int(value) for value in non_empty):
            return "BIGINT"
        if all(self._is_decimal(value) for value in non_empty):
            return "DECIMAL(24, 6)"
        if all(self._is_date(value) for value in non_empty):
            return "DATETIME"
        max_length = max(len(value) for value in non_empty)
        return f"VARCHAR({min(max(max_length * 2, 64), 512)})" if max_length <= 255 else "TEXT"

    def _create_table(self, table_name: str, columns: list[ColumnSpec]) -> None:
        column_sql = ",\n  ".join(f"`{column.sql_name}` {column.mysql_type} NULL" for column in columns)
        create_sql = f"""
CREATE TABLE `{table_name}` (
  `id` BIGINT PRIMARY KEY AUTO_INCREMENT,
  {column_sql}
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
""".strip()
        with engine.begin() as connection:
            connection.execute(text(create_sql))

    def _insert_rows(self, table_name: str, columns: list[ColumnSpec], rows: list[dict[str, str]]) -> int:
        column_names = [column.sql_name for column in columns]
        sql = text(
            f"INSERT INTO `{table_name}` ({', '.join(f'`{name}`' for name in column_names)}) "
            f"VALUES ({', '.join(f':{name}' for name in column_names)})"
        )
        payload = []
        for row in rows:
            item = {}
            for column in columns:
                value = str(row.get(column.original_name, "")).strip()
                item[column.sql_name] = self._convert_value(value, column.mysql_type)
            payload.append(item)
        with engine.begin() as connection:
            connection.execute(sql, payload)
        return len(payload)

    def _upsert_metadata(
        self,
        table_name: str,
        display_name: str,
        filename: str,
        columns: list[ColumnSpec],
        rows: list[dict[str, str]],
        row_count: int,
    ) -> None:
        with SessionLocal() as session:
            self._delete_metadata(session, table_name)
            session.add(
                MetadataCatalog(
                    object_type="uploaded_table",
                    object_name=table_name,
                    parent_name=None,
                    business_name=display_name,
                    description=f"用户上传的 CSV 数据集，来源文件 {filename}，已导入 {row_count} 行，可作为自由查询表使用。",
                    synonyms=f"{display_name},{filename},CSV,上传数据,用户数据,{table_name}",
                    example_values=self._example_row(columns, rows),
                )
            )
            for column in columns:
                session.add(
                    MetadataCatalog(
                        object_type="uploaded_column",
                        object_name=f"{table_name}.{column.sql_name}",
                        parent_name=table_name,
                        business_name=column.original_name,
                        description=f"上传数据集 {display_name} 的列，原始列名为 {column.original_name}，SQL 列名为 {column.sql_name}，类型为 {column.mysql_type}。",
                        synonyms=f"{column.original_name},{column.sql_name},{display_name},{table_name}",
                        example_values=self._example_values(column.original_name, rows),
                    )
                )
            session.commit()

    def _delete_metadata(self, session, table_name: str) -> None:
        rows = session.query(MetadataCatalog).filter(
            (MetadataCatalog.object_name == table_name)
            | (MetadataCatalog.parent_name == table_name)
            | (MetadataCatalog.object_name.like(f"{table_name}.%"))
        )
        rows.delete(synchronize_session=False)

    def _example_row(self, columns: list[ColumnSpec], rows: list[dict[str, str]]) -> str:
        if not rows:
            return ""
        first = rows[0]
        parts = []
        for column in columns[:8]:
            value = str(first.get(column.original_name, "")).strip()
            if value:
                parts.append(f"{column.original_name}={value}")
        return "; ".join(parts)

    def _example_values(self, original_name: str, rows: list[dict[str, str]]) -> str:
        values = []
        for row in rows[:8]:
            value = str(row.get(original_name, "")).strip()
            if value and value not in values:
                values.append(value)
        return ", ".join(values[:5])

    def _convert_value(self, value: str, mysql_type: str):
        if value == "":
            return None
        if mysql_type == "BIGINT":
            return int(Decimal(value.replace(",", "")))
        if mysql_type.startswith("DECIMAL"):
            return Decimal(value.replace(",", ""))
        if mysql_type == "DATETIME":
            return self._parse_date(value)
        return value

    def _is_int(self, value: str) -> bool:
        try:
            Decimal(value.replace(",", ""))
        except InvalidOperation:
            return False
        return "." not in value

    def _is_decimal(self, value: str) -> bool:
        try:
            Decimal(value.replace(",", ""))
            return True
        except InvalidOperation:
            return False

    def _is_date(self, value: str) -> bool:
        return self._parse_date(value) is not None

    def _parse_date(self, value: str):
        for pattern in DATE_PATTERNS:
            try:
                return datetime.strptime(value, pattern)
            except ValueError:
                continue
        return None
