from __future__ import annotations

import json
import math
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from statistics import mean, pstdev
from typing import Any, Callable

from app.core.config import PROJECT_ROOT


EXTENSIONS_ROOT = PROJECT_ROOT / "agent_extensions"
SKILLS_DIR = EXTENSIONS_ROOT / "skills"
TOOLS_DIR = EXTENSIONS_ROOT / "tools"


@dataclass(frozen=True)
class SkillDefinition:
    name: str
    display_name: str
    description: str
    routes: list[str]
    keywords: list[str]
    tools: list[str]
    prompt_hint: str = ""


@dataclass(frozen=True)
class ToolDefinition:
    name: str
    display_name: str
    description: str
    function: str
    input_hint: str = ""


class SkillToolManager:
    def __init__(self) -> None:
        self.tool_functions: dict[str, Callable[[list[dict[str, Any]], list[str]], dict[str, Any]]] = {
            "moving_average_trend": self._moving_average_trend,
            "return_risk_summary": self._return_risk_summary,
            "valuation_snapshot": self._valuation_snapshot,
            "dataset_profile": self._dataset_profile,
        }

    def list_extensions(self) -> dict[str, list[dict[str, Any]]]:
        return {
            "skills": [skill.__dict__ for skill in self._load_skills()],
            "tools": [tool.__dict__ for tool in self._load_tools()],
        }

    def run(
        self,
        *,
        question: str,
        route: str,
        rows: list[dict[str, Any]],
        columns: list[str],
    ) -> dict[str, Any]:
        skills = self._match_skills(question, route)
        tools = {tool.name: tool for tool in self._load_tools()}
        tool_results: list[dict[str, Any]] = []
        used_tools: set[str] = set()

        for skill in skills:
            for tool_name in skill.tools:
                if tool_name in used_tools:
                    continue
                tool = tools.get(tool_name)
                if not tool:
                    continue
                function = self.tool_functions.get(tool.function)
                if not function:
                    continue
                used_tools.add(tool_name)
                try:
                    output = function(rows, columns)
                except Exception as exc:
                    output = {"ok": False, "summary": f"工具执行失败：{exc}"}
                tool_results.append(
                    {
                        "name": tool.name,
                        "display_name": tool.display_name,
                        "description": tool.description,
                        "output": output,
                    }
                )

        return {
            "matched_skills": [
                {
                    "name": skill.name,
                    "display_name": skill.display_name,
                    "description": skill.description,
                    "prompt_hint": skill.prompt_hint,
                    "tools": skill.tools,
                }
                for skill in skills
            ],
            "tool_results": tool_results,
        }

    def _match_skills(self, question: str, route: str) -> list[SkillDefinition]:
        lowered = question.lower()
        scored: list[tuple[int, SkillDefinition]] = []
        for skill in self._load_skills():
            if skill.routes and route not in skill.routes:
                continue
            score = sum(1 for keyword in skill.keywords if keyword.lower() in lowered)
            if score:
                scored.append((score, skill))
        scored.sort(key=lambda item: item[0], reverse=True)
        return [skill for _, skill in scored[:3]]

    def _load_skills(self) -> list[SkillDefinition]:
        return [
            SkillDefinition(
                name=str(raw.get("name")),
                display_name=str(raw.get("display_name") or raw.get("name")),
                description=str(raw.get("description") or ""),
                routes=list(raw.get("routes") or []),
                keywords=list(raw.get("keywords") or []),
                tools=list(raw.get("tools") or []),
                prompt_hint=str(raw.get("prompt_hint") or ""),
            )
            for raw in self._load_json_files(SKILLS_DIR)
            if raw.get("name")
        ]

    def _load_tools(self) -> list[ToolDefinition]:
        return [
            ToolDefinition(
                name=str(raw.get("name")),
                display_name=str(raw.get("display_name") or raw.get("name")),
                description=str(raw.get("description") or ""),
                function=str(raw.get("function") or raw.get("name")),
                input_hint=str(raw.get("input_hint") or ""),
            )
            for raw in self._load_json_files(TOOLS_DIR)
            if raw.get("name")
        ]

    def _load_json_files(self, directory: Path) -> list[dict[str, Any]]:
        if not directory.exists():
            return []
        items: list[dict[str, Any]] = []
        for path in sorted(directory.glob("*.json")):
            try:
                items.append(json.loads(path.read_text(encoding="utf-8")))
            except Exception:
                continue
        return items

    def _moving_average_trend(self, rows: list[dict[str, Any]], columns: list[str]) -> dict[str, Any]:
        series = self._numeric_series(rows, columns)
        if not series:
            return {"ok": False, "summary": "没有找到可用于趋势分析的数值字段。"}
        values = [item["value"] for item in series]
        first, latest = values[0], values[-1]
        change = latest - first
        change_pct = self._safe_pct(change, first)
        ma5 = mean(values[-5:]) if len(values) >= 5 else mean(values)
        ma10 = mean(values[-10:]) if len(values) >= 10 else mean(values)
        trend = "上升" if latest > ma5 else "走弱" if latest < ma5 else "持平"
        return {
            "ok": True,
            "field": series[0]["field"],
            "points": len(values),
            "latest": round(latest, 4),
            "first": round(first, 4),
            "change": round(change, 4),
            "change_pct": round(change_pct, 4) if change_pct is not None else None,
            "ma5": round(ma5, 4),
            "ma10": round(ma10, 4),
            "trend": trend,
            "summary": f"{series[0]['field']} 最新值 {latest:.4g}，相对区间首值变化 {change:.4g}，短期趋势判断为{trend}。",
        }

    def _return_risk_summary(self, rows: list[dict[str, Any]], columns: list[str]) -> dict[str, Any]:
        series = self._numeric_series(rows, columns)
        if not series:
            return {"ok": False, "summary": "没有找到可用于收益风险分析的数值字段。"}
        values = [item["value"] for item in series]
        if len(values) < 2:
            return {"ok": False, "summary": "数据点不足，至少需要 2 个数值点。"}
        returns = [
            (values[index] - values[index - 1]) / values[index - 1]
            for index in range(1, len(values))
            if values[index - 1] != 0
        ]
        max_drawdown = self._max_drawdown(values)
        volatility = pstdev(returns) if len(returns) >= 2 else 0.0
        total_return = self._safe_pct(values[-1] - values[0], values[0])
        return {
            "ok": True,
            "field": series[0]["field"],
            "points": len(values),
            "total_return": round(total_return, 4) if total_return is not None else None,
            "volatility": round(volatility, 4),
            "max_drawdown": round(max_drawdown, 4),
            "min": round(min(values), 4),
            "max": round(max(values), 4),
            "summary": f"{series[0]['field']} 区间收益约 {self._pct_text(total_return)}，波动率约 {volatility:.2%}，最大回撤约 {max_drawdown:.2%}。",
        }

    def _valuation_snapshot(self, rows: list[dict[str, Any]], columns: list[str]) -> dict[str, Any]:
        series = self._numeric_series(rows, columns, preferred=["factor_value", "metric_value", "pe_ttm", "roe", "net_profit", "revenue"])
        if not series:
            return {"ok": False, "summary": "没有找到可用于估值或财务指标分析的数值字段。"}
        values = [item["value"] for item in series]
        min_item = min(series, key=lambda item: item["value"])
        max_item = max(series, key=lambda item: item["value"])
        return {
            "ok": True,
            "field": series[0]["field"],
            "count": len(values),
            "average": round(mean(values), 4),
            "min": self._label_row(min_item),
            "max": self._label_row(max_item),
            "summary": f"{series[0]['field']} 共 {len(values)} 条，均值 {mean(values):.4g}，最低为 {self._label_row(min_item)}，最高为 {self._label_row(max_item)}。",
        }

    def _dataset_profile(self, rows: list[dict[str, Any]], columns: list[str]) -> dict[str, Any]:
        numeric_fields = []
        missing_count = 0
        for column in columns:
            values = [row.get(column) for row in rows]
            missing_count += sum(1 for value in values if value in (None, ""))
            numeric_values = [self._to_float(value) for value in values]
            numeric_values = [value for value in numeric_values if value is not None]
            if numeric_values:
                numeric_fields.append(
                    {
                        "field": column,
                        "min": round(min(numeric_values), 4),
                        "max": round(max(numeric_values), 4),
                        "average": round(mean(numeric_values), 4),
                    }
                )
        return {
            "ok": True,
            "row_count": len(rows),
            "column_count": len(columns),
            "missing_count": missing_count,
            "numeric_fields": numeric_fields[:8],
            "sample_columns": columns[:12],
            "summary": f"当前结果包含 {len(rows)} 行、{len(columns)} 列，空值 {missing_count} 个，识别到 {len(numeric_fields)} 个数值字段。",
        }

    def _numeric_series(
        self,
        rows: list[dict[str, Any]],
        columns: list[str],
        preferred: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        if not rows:
            return []
        preferred = preferred or [
            "close_price",
            "metric_value",
            "factor_value",
            "open_price",
            "high_price",
            "low_price",
            "turnover",
            "volume",
        ]
        column = next((name for name in preferred if name in columns), None)
        if column is None:
            column = next((name for name in columns if any(self._to_float(row.get(name)) is not None for row in rows)), None)
        if column is None:
            return []
        date_column = next((name for name in ["trade_date", "report_period", "period", "date"] if name in columns), None)
        series = []
        for index, row in enumerate(rows):
            value = self._to_float(row.get(column))
            if value is None or math.isnan(value):
                continue
            series.append(
                {
                    "field": column,
                    "value": value,
                    "label": self._row_label(row),
                    "date": str(row.get(date_column) or index),
                }
            )
        return sorted(series, key=lambda item: item["date"])

    def _row_label(self, row: dict[str, Any]) -> str:
        symbol = row.get("symbol")
        name = row.get("name")
        date_value = row.get("trade_date") or row.get("report_period") or row.get("period")
        parts = [str(item) for item in [name, symbol, date_value] if item not in (None, "")]
        return " ".join(parts) if parts else "样本"

    def _label_row(self, item: dict[str, Any]) -> str:
        return f"{item['label']} ({item['value']:.4g})"

    def _to_float(self, value: Any) -> float | None:
        if value in (None, ""):
            return None
        if isinstance(value, (int, float)):
            return float(value)
        if isinstance(value, Decimal):
            return float(value)
        if isinstance(value, (datetime, date)):
            return None
        try:
            return float(str(value).replace(",", ""))
        except ValueError:
            return None

    def _safe_pct(self, diff: float, base: float) -> float | None:
        if base == 0:
            return None
        return diff / base

    def _pct_text(self, value: float | None) -> str:
        return "不可计算" if value is None else f"{value:.2%}"

    def _max_drawdown(self, values: list[float]) -> float:
        peak = values[0]
        drawdown = 0.0
        for value in values:
            peak = max(peak, value)
            if peak:
                drawdown = max(drawdown, (peak - value) / peak)
        return drawdown
