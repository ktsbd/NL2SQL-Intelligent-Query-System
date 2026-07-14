import re
from calendar import monthrange
from datetime import date

from sqlalchemy import select

from app.db.models import MetadataCatalog, Stock
from app.db.session import SessionLocal


def u(value: str) -> str:
    return value.encode("ascii").decode("unicode_escape")


STOCK_ALIASES = {
    u("\\u8d35\\u5dde\\u8305\\u53f0"): "600519",
    u("\\u8305\\u53f0"): "600519",
    u("\\u5e73\\u5b89\\u94f6\\u884c"): "000001",
    u("\\u5b81\\u5fb7\\u65f6\\u4ee3"): "300750",
    u("\\u4e2d\\u56fd\\u5e73\\u5b89"): "601318",
    u("\\u62db\\u5546\\u94f6\\u884c"): "600036",
    u("\\u62db\\u884c"): "600036",
    u("\\u6d77\\u5eb7\\u5a01\\u89c6"): "002415",
}

INDUSTRY_ALIASES = [
    u("\\u94f6\\u884c"),
    u("\\u98df\\u54c1\\u996e\\u6599"),
    u("\\u7535\\u529b\\u8bbe\\u5907"),
    u("\\u8ba1\\u7b97\\u673a"),
    u("\\u975e\\u94f6\\u91d1\\u878d"),
]

MARKET_KEYWORDS = [u("\\u6536\\u76d8\\u4ef7"), u("\\u5f00\\u76d8\\u4ef7"), u("\\u6700\\u9ad8\\u4ef7"), u("\\u6700\\u4f4e\\u4ef7"), u("\\u6210\\u4ea4\\u91cf"), u("\\u6210\\u4ea4\\u989d"), u("\\u884c\\u60c5"), u("\\u4ef7\\u683c")]
FACTOR_KEYWORDS = ["pe", u("\\u5e02\\u76c8\\u7387"), u("\\u4f30\\u503c"), u("\\u56e0\\u5b50"), u("\\u52a8\\u91cf"), "momentum"]
BUSINESS_KEYWORDS = [u("\\u88c5\\u673a\\u91cf"), u("\\u4e0d\\u826f\\u8d37\\u6b3e\\u7387"), u("\\u4e0d\\u826f\\u7387"), u("\\u5e93\\u5b58\\u5468\\u8f6c"), u("\\u7efc\\u5408\\u6210\\u672c\\u7387"), u("\\u6d77\\u5916\\u6536\\u5165"), u("\\u4e1a\\u52a1\\u6307\\u6807"), u("\\u7ecf\\u8425\\u6307\\u6807")]
FINANCIAL_KEYWORDS = [u("\\u51c0\\u5229\\u6da6"), u("\\u5229\\u6da6"), "roe", u("\\u51c0\\u8d44\\u4ea7\\u6536\\u76ca\\u7387"), u("\\u6bdb\\u5229\\u7387"), u("\\u6536\\u5165"), u("\\u8425\\u6536"), u("\\u8d44\\u4ea7"), u("\\u8d1f\\u503a"), u("\\u8d22\\u52a1")]


class NL2SQLGenerator:
    def generate(self, question: str, limit: int = 10) -> tuple[str, str, dict[str, object]]:
        normalized = question.lower()

        if self._contains_any(question, MARKET_KEYWORDS):
            return self._market_sql(question, limit)

        if self._contains_any(question, FACTOR_KEYWORDS):
            return self._factor_sql(question, limit)

        if self._contains_any(question, BUSINESS_KEYWORDS):
            return self._business_metric_sql(question, limit)

        if self._contains_any(question, FINANCIAL_KEYWORDS):
            return self._financial_sql(question, normalized, limit)

        return self._stock_sql(question, limit)

    def generate_uploaded(self, question: str, context: list[dict[str, object]], limit: int) -> tuple[str, str, dict[str, object]] | None:
        if not self._should_use_uploaded_dataset(question, context):
            return None
        table_name = self._pick_uploaded_table(context)
        if not table_name:
            return None
        columns = self._uploaded_columns(table_name)
        if not columns:
            return None

        selected = self._selected_uploaded_columns(question, columns)
        if not selected:
            selected = columns[:12]
        order_column = self._order_uploaded_column(question, selected, columns)
        direction = self._direction(question)
        select_sql = ",\n  ".join(f"`{column}`" for column in selected)
        order_sql = f"\nORDER BY `{order_column}` {direction}" if order_column else ""
        sql = f"""
SELECT
  {select_sql}
FROM `{table_name}`{order_sql}
LIMIT :limit
""".strip()
        return f"uploaded_dataset:{table_name}", sql, {"limit": limit}

    def _should_use_uploaded_dataset(self, question: str, context: list[dict[str, object]]) -> bool:
        uploaded_keywords = ["上传", "csv", "CSV", "我的数据", "导入", "数据集", "uploaded"]
        if self._contains_any(question, uploaded_keywords):
            return True
        if not context:
            return False
        top = context[0]
        object_name = str(top.get("object_name", ""))
        object_type = str(top.get("object_type", ""))
        return object_name.startswith("uploaded_") and object_type == "uploaded_table" and float(top.get("rank_score", 0.0)) >= 1.2

    def _financial_sql(self, question: str, normalized: str, limit: int) -> tuple[str, str, dict[str, object]]:
        metric = "net_profit"
        metric_label = u("\\u51c0\\u5229\\u6da6")
        if "roe" in normalized or u("\\u51c0\\u8d44\\u4ea7\\u6536\\u76ca\\u7387") in question:
            metric = "roe"
            metric_label = "ROE"
        elif u("\\u6bdb\\u5229\\u7387") in question:
            metric = "gross_margin"
            metric_label = u("\\u6bdb\\u5229\\u7387")
        elif self._contains_any(question, [u("\\u6536\\u5165"), u("\\u8425\\u6536")]):
            metric = "revenue"
            metric_label = u("\\u6536\\u5165")
        elif u("\\u8d44\\u4ea7") in question and u("\\u8d1f\\u503a") not in question:
            metric = "total_assets"
            metric_label = u("\\u603b\\u8d44\\u4ea7")
        elif u("\\u8d1f\\u503a") in question:
            metric = "total_liabilities"
            metric_label = u("\\u603b\\u8d1f\\u503a")

        direction = self._direction(question)
        where_sql, params = self._filters(question)
        params["limit"] = limit
        sql = f"""
SELECT
  s.symbol,
  s.name,
  s.industry,
  f.report_period,
  f.{metric} AS metric_value
FROM financial_statements f
JOIN stocks s ON s.id = f.stock_id
{where_sql}
ORDER BY f.{metric} {direction}
LIMIT :limit
""".strip()
        return f"financial_metric:{metric_label}", sql, params

    def _market_sql(self, question: str, limit: int) -> tuple[str, str, dict[str, object]]:
        direction = self._direction(question)
        order_column = "close_price"
        if u("\\u5f00\\u76d8\\u4ef7") in question:
            order_column = "open_price"
        elif u("\\u6700\\u9ad8\\u4ef7") in question:
            order_column = "high_price"
        elif u("\\u6700\\u4f4e\\u4ef7") in question:
            order_column = "low_price"
        elif u("\\u6210\\u4ea4\\u91cf") in question:
            order_column = "volume"
        elif u("\\u6210\\u4ea4\\u989d") in question:
            order_column = "turnover"

        where_sql, params = self._filters(question)
        date_sql, date_params = self._market_date_filter(question)
        if date_sql:
            where_sql = self._append_condition(where_sql, date_sql)
            params.update(date_params)
        params["limit"] = limit
        sql = f"""
SELECT
  s.symbol,
  s.name,
  m.trade_date,
  m.open_price,
  m.close_price,
  m.high_price,
  m.low_price,
  m.volume,
  m.turnover
FROM daily_market m
JOIN stocks s ON s.id = m.stock_id
{where_sql}
ORDER BY m.{order_column} {direction}
LIMIT :limit
""".strip()
        return f"daily_market:{order_column}", sql, params

    def _factor_sql(self, question: str, limit: int) -> tuple[str, str, dict[str, object]]:
        factor_name = "pe_ttm"
        if self._contains_any(question, [u("\\u52a8\\u91cf"), "momentum", u("\\u8d8b\\u52bf")]):
            factor_name = "momentum_20d"
        direction = self._direction(question)
        if factor_name == "pe_ttm" and self._contains_any(question, [u("\\u4f4e\\u4f30"), u("\\u4fbf\\u5b9c"), u("\\u6700\\u4f4e"), u("\\u8f83\\u4f4e"), u("\\u4f4e\\u5e02\\u76c8\\u7387")]):
            direction = "ASC"
        where_sql, params = self._filters(question, prefix=" AND ")
        params.update({"factor_name": factor_name, "limit": limit})
        sql = f"""
SELECT
  s.symbol,
  s.name,
  s.industry,
  fv.trade_date,
  fv.factor_name,
  fv.factor_value
FROM factor_values fv
JOIN stocks s ON s.id = fv.stock_id
WHERE fv.factor_name = :factor_name{where_sql}
ORDER BY fv.factor_value {direction}
LIMIT :limit
""".strip()
        return f"factor:{factor_name}", sql, params

    def _business_metric_sql(self, question: str, limit: int) -> tuple[str, str, dict[str, object]]:
        metric_name = self._pick_business_metric(question)
        direction = "ASC" if self._contains_any(question, [u("\\u6700\\u4f4e"), u("\\u6700\\u5c11"), u("\\u8f83\\u4f4e"), u("\\u66f4\\u4f4e"), u("\\u4f4e")]) else "DESC"
        where_sql, params = self._filters(question, prefix=" AND ")
        params.update({"metric_name": f"%{metric_name}%", "limit": limit})
        sql = f"""
SELECT
  s.symbol,
  s.name,
  s.industry,
  bm.period,
  bm.metric_name,
  bm.metric_value,
  bm.unit
FROM business_metrics bm
JOIN stocks s ON s.id = bm.stock_id
WHERE bm.metric_name LIKE :metric_name{where_sql}
ORDER BY bm.metric_value {direction}
LIMIT :limit
""".strip()
        return f"business_metric:{metric_name}", sql, params

    def _stock_sql(self, question: str, limit: int) -> tuple[str, str, dict[str, object]]:
        where_sql, params = self._filters(question)
        params["limit"] = limit
        sql = f"""
SELECT
  s.symbol,
  s.name,
  s.exchange,
  s.industry,
  s.listed_date
FROM stocks s
{where_sql}
ORDER BY s.symbol
LIMIT :limit
""".strip()
        return "stock_profile", sql, params

    def _filters(self, question: str, prefix: str = "WHERE ") -> tuple[str, dict[str, object]]:
        conditions = []
        params: dict[str, object] = {}
        stock_symbol = self._pick_stock(question)
        if stock_symbol:
            conditions.append("s.symbol = :symbol")
            params["symbol"] = stock_symbol
        industry = self._pick_industry(question)
        if industry:
            conditions.append("s.industry = :industry")
            params["industry"] = industry
        if not conditions:
            return "", params
        return prefix + " AND ".join(conditions), params

    def _pick_stock(self, question: str) -> str | None:
        symbol_match = re.search(r"(?<!\d)(\d{6})(?!\d)", question)
        if symbol_match:
            return symbol_match.group(1)
        for alias, symbol in STOCK_ALIASES.items():
            if alias in question or symbol in question:
                return symbol
        with SessionLocal() as session:
            stocks = session.execute(select(Stock.symbol, Stock.name)).all()
            for symbol, name in stocks:
                if name and name in question:
                    return symbol
        return None

    def _pick_industry(self, question: str) -> str | None:
        for industry in INDUSTRY_ALIASES:
            if industry in question:
                return industry
        return None

    def _pick_business_metric(self, question: str) -> str:
        if u("\\u88c5\\u673a\\u91cf") in question:
            return u("\\u52a8\\u529b\\u7535\\u6c60\\u88c5\\u673a\\u91cf")
        if self._contains_any(question, [u("\\u4e0d\\u826f\\u8d37\\u6b3e\\u7387"), u("\\u4e0d\\u826f\\u7387")]):
            return u("\\u4e0d\\u826f\\u8d37\\u6b3e\\u7387")
        if self._contains_any(question, [u("\\u5e93\\u5b58\\u5468\\u8f6c"), u("\\u5468\\u8f6c\\u5929\\u6570")]):
            return u("\\u6e20\\u9053\\u5e93\\u5b58\\u5468\\u8f6c\\u5929\\u6570")
        if u("\\u7efc\\u5408\\u6210\\u672c\\u7387") in question:
            return u("\\u7efc\\u5408\\u6210\\u672c\\u7387")
        if u("\\u6d77\\u5916\\u6536\\u5165") in question:
            return u("\\u6d77\\u5916\\u6536\\u5165\\u5360\\u6bd4")
        match = re.search(r"[\u4e00-\u9fff]{2,12}", question)
        return match.group(0) if match else "business_metric"

    def _pick_uploaded_table(self, context: list[dict[str, object]]) -> str | None:
        for item in context:
            object_type = str(item.get("object_type", ""))
            object_name = str(item.get("object_name", ""))
            parent_name = item.get("parent_name")
            if object_type == "uploaded_table" and object_name.startswith("uploaded_"):
                return object_name
            if object_type == "uploaded_column" and parent_name and str(parent_name).startswith("uploaded_"):
                return str(parent_name)
        return None

    def _uploaded_columns(self, table_name: str) -> list[str]:
        with SessionLocal() as session:
            rows = session.execute(
                select(MetadataCatalog.object_name)
                .where(MetadataCatalog.object_type == "uploaded_column")
                .where(MetadataCatalog.parent_name == table_name)
                .order_by(MetadataCatalog.id)
            ).all()
        return [str(row[0]).split(".", 1)[1] for row in rows if "." in str(row[0])]

    def _selected_uploaded_columns(self, question: str, columns: list[str]) -> list[str]:
        lowered = question.lower()
        selected = [column for column in columns if column.lower() in lowered]
        with SessionLocal() as session:
            metadata_rows = session.execute(
                select(MetadataCatalog.object_name, MetadataCatalog.business_name)
                .where(MetadataCatalog.object_type == "uploaded_column")
            ).all()
        for object_name, business_name in metadata_rows:
            column = str(object_name).split(".", 1)[-1]
            if column in columns and str(business_name) in question and column not in selected:
                selected.append(column)
        return selected

    def _order_uploaded_column(self, question: str, selected: list[str], columns: list[str]) -> str | None:
        ordered_keywords = [u("\\u6700\\u9ad8"), u("\\u6700\\u4f4e"), u("\\u6700\\u5927"), u("\\u6700\\u5c0f"), u("\\u6392\\u5e8f"), "top"]
        if not self._contains_any(question, ordered_keywords):
            return None
        for column in selected + columns:
            if column.lower() in question.lower():
                return column
        numeric_hints = ["amount", "price", "volume", "close", "open", "high", "low", "value", "rate", "ratio", "pct"]
        for column in columns:
            if any(hint in column.lower() for hint in numeric_hints):
                return column
        return selected[0] if selected else columns[0]

    def _direction(self, question: str) -> str:
        return "ASC" if self._contains_any(question, [u("\\u6700\\u4f4e"), u("\\u6700\\u5c11"), u("\\u6700\\u5c0f"), u("\\u8f83\\u4f4e"), u("\\u66f4\\u4f4e"), u("\\u5347\\u5e8f"), u("\\u4f4e\\u4f30")]) else "DESC"

    def _contains_any(self, text: str, keywords: list[str]) -> bool:
        lowered = text.lower()
        return any(keyword.lower() in lowered for keyword in keywords)

    def _market_date_filter(self, question: str) -> tuple[str, dict[str, object]]:
        full_date = self._extract_full_date(question)
        if full_date:
            return "m.trade_date = :trade_date", {"trade_date": full_date}
        year_month = self._extract_year_month(question)
        if year_month:
            year, month = year_month
            return "m.trade_date BETWEEN :start_date AND :end_date", {
                "start_date": date(year, month, 1),
                "end_date": date(year, month, monthrange(year, month)[1]),
            }
        year = self._extract_year(question)
        if year:
            return "m.trade_date BETWEEN :start_date AND :end_date", {
                "start_date": date(year, 1, 1),
                "end_date": date(year, 12, 31),
            }
        return "", {}

    def _extract_full_date(self, question: str) -> date | None:
        patterns = [
            r"(?P<year>20\d{2})[-/.\u5e74](?P<month>\d{1,2})[-/.\u6708](?P<day>\d{1,2})\u65e5?",
            r"(?<!\d)(?P<year>20\d{2})(?P<month>\d{2})(?P<day>\d{2})(?!\d)",
        ]
        for pattern in patterns:
            match = re.search(pattern, question)
            if match:
                return date(int(match.group("year")), int(match.group("month")), int(match.group("day")))
        return None

    def _extract_year_month(self, question: str) -> tuple[int, int] | None:
        patterns = [
            r"(?P<year>20\d{2})[-/.\u5e74](?P<month>\d{1,2})\u6708?",
            r"(?<!\d)(?P<year>20\d{2})(?P<month>\d{2})(?!\d)",
        ]
        for pattern in patterns:
            match = re.search(pattern, question)
            if match:
                month = int(match.group("month"))
                if 1 <= month <= 12:
                    return int(match.group("year")), month
        return None

    def _extract_year(self, question: str) -> int | None:
        match = re.search(r"(?P<year>20\d{2})\u5e74?", question)
        return int(match.group("year")) if match else None

    def _append_condition(self, where_sql: str, condition: str) -> str:
        if not where_sql:
            return f"WHERE {condition}"
        return f"{where_sql} AND {condition}"
