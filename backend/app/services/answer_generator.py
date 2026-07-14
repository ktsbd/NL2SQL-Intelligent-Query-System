from __future__ import annotations

import json
from decimal import Decimal
from typing import Any

from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from app.core.config import settings


class AnswerGenerator:
    def __init__(self) -> None:
        self.enabled = bool(settings.openai_api_key and settings.openai_api_key != "replace_with_your_key")
        self.prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "你是金融数据智能查询系统的中文助手。"
                    "回答必须基于提供的 SQL 查询结果和短期历史，不要编造不存在的数据。"
                    "如果提供了工具分析结果，要优先参考这些结构化结论。"
                    "如果结果为空，要说明没有查到匹配数据，并给出可以继续追问的方向。"
                    "如果是分析类问题，先概括结论，再列出关键依据和风险提示。"
                    "这不是投资建议，不要给出确定性买卖建议。",
                ),
                (
                    "human",
                    "路由：{route}\n用户问题：{question}\n短期历史：\n{history}\nSQL：\n{sql}\n查询结果 JSON：\n{rows}\n工具分析结果 JSON：\n{tool_results}\n请自然语言回答。",
                ),
            ]
        )

    def answer(
        self,
        *,
        route: str,
        question: str,
        history: list[dict[str, str]],
        sql: str = "",
        rows: list[dict[str, Any]] | None = None,
        tool_results: list[dict[str, Any]] | None = None,
    ) -> str:
        rows = rows or []
        tool_results = tool_results or []
        if self.enabled:
            try:
                llm = ChatOpenAI(
                    model=settings.openai_model,
                    api_key=settings.openai_api_key,
                    base_url=settings.openai_base_url or None,
                    temperature=0.2,
                )
                chain = self.prompt | llm
                response = chain.invoke(
                    {
                        "route": route,
                        "question": question,
                        "history": self._format_history(history),
                        "sql": sql or "未执行 SQL",
                        "rows": self._format_rows(rows),
                        "tool_results": self._format_tool_results(tool_results),
                    }
                )
                return str(response.content).strip()
            except Exception:
                return self._fallback_answer(route, question, sql, rows, tool_results)
        return self._fallback_answer(route, question, sql, rows, tool_results)

    def answer_plan(
        self,
        *,
        question: str,
        history: list[dict[str, str]],
        plan_results: list[dict[str, Any]],
    ) -> str:
        if self.enabled:
            try:
                prompt = ChatPromptTemplate.from_messages(
                    [
                        (
                            "system",
                            "你是金融数据 Agent 的中文分析助手。你会收到一个多步骤分析计划的执行结果。"
                            "必须基于 SQL 查询结果和工具结果回答，不要编造数据。"
                            "回答结构：先给总论，再按行情/估值/财务/风险等维度列证据，最后给风险提示。"
                            "这不是投资建议，不要给确定性买卖建议。",
                        ),
                        (
                            "human",
                            "用户问题：{question}\n短期历史：\n{history}\n多步骤执行结果 JSON：\n{plan_results}\n请输出综合分析。",
                        ),
                    ]
                )
                response = (
                    prompt
                    | ChatOpenAI(
                        model=settings.openai_model,
                        api_key=settings.openai_api_key,
                        base_url=settings.openai_base_url or None,
                        temperature=0.2,
                    )
                ).invoke(
                    {
                        "question": question,
                        "history": self._format_history(history),
                        "plan_results": json.dumps(plan_results, ensure_ascii=False, default=self._json_default, indent=2),
                    }
                )
                return str(response.content).strip()
            except Exception:
                pass
        return self._fallback_plan_answer(question, plan_results)

    def general_chat(self, message: str, history: list[dict[str, str]]) -> str:
        if self.enabled:
            try:
                prompt = ChatPromptTemplate.from_messages(
                    [
                        (
                            "system",
                            "你是 NL2SQL 金融数据智能查询系统的助手。"
                            "可以解释系统使用方式，也可以提醒用户上传 CSV 或询问股票/财务/因子数据。",
                        ),
                        ("human", "短期历史：\n{history}\n用户：{message}"),
                    ]
                )
                response = (
                    prompt
                    | ChatOpenAI(
                        model=settings.openai_model,
                        api_key=settings.openai_api_key,
                        base_url=settings.openai_base_url or None,
                        temperature=0.3,
                    )
                ).invoke(
                    {"history": self._format_history(history), "message": message}
                )
                return str(response.content).strip()
            except Exception:
                pass
        return "我可以帮你查询股票行情、财务指标、因子指标，也可以在你上传 CSV 后用自然语言查询这份数据。你可以问：贵州茅台最近行情如何？"

    def _fallback_answer(
        self,
        route: str,
        question: str,
        sql: str,
        rows: list[dict[str, Any]],
        tool_results: list[dict[str, Any]] | None = None,
    ) -> str:
        tool_results = tool_results or []
        tool_summary = self._fallback_tool_summary(tool_results)
        if not rows:
            return "没有查到匹配的数据。你可以换一个股票、指标、时间范围，或先上传带表头的 CSV 数据。"
        first_rows = rows[:3]
        if route == "data_analysis":
            return f"已基于查询结果做初步分析：本次返回 {len(rows)} 行数据。{tool_summary}前几条关键记录为 {self._format_rows(first_rows)}。"
        return f"查询完成，共返回 {len(rows)} 行数据。{tool_summary}前几条结果：{self._format_rows(first_rows)}"

    def _fallback_plan_answer(self, question: str, plan_results: list[dict[str, Any]]) -> str:
        parts = [f"已按多步骤计划分析：{question}"]
        for item in plan_results:
            rows = item.get("rows") or []
            tool_results = item.get("tool_results") or []
            summaries = []
            for tool in tool_results:
                output = tool.get("output") if isinstance(tool, dict) else {}
                if isinstance(output, dict) and output.get("summary"):
                    summaries.append(str(output["summary"]))
            parts.append(
                f"{item.get('name', 'task')}：返回 {len(rows)} 行；"
                + ("；".join(summaries[:2]) if summaries else "暂无工具摘要")
            )
        parts.append("以上仅基于当前数据库查询结果，不构成投资建议。")
        return "\n".join(parts)

    def _format_history(self, history: list[dict[str, str]]) -> str:
        return "\n".join(
            json.dumps({"role": item["role"], "content": item["content"]}, ensure_ascii=False)
            for item in history[-8:]
        )

    def _format_rows(self, rows: list[dict[str, Any]]) -> str:
        return json.dumps(rows[:20], ensure_ascii=False, default=self._json_default, indent=2)

    def _format_tool_results(self, tool_results: list[dict[str, Any]]) -> str:
        return json.dumps(tool_results, ensure_ascii=False, default=self._json_default, indent=2)

    def _fallback_tool_summary(self, tool_results: list[dict[str, Any]]) -> str:
        summaries = []
        for item in tool_results:
            output = item.get("output") or {}
            summary = output.get("summary") if isinstance(output, dict) else None
            if summary:
                summaries.append(f"{item.get('display_name', item.get('name'))}：{summary}")
        if not summaries:
            return ""
        return "工具分析结果：" + "；".join(summaries[:3]) + "。"

    def _json_default(self, value: Any) -> str:
        if isinstance(value, Decimal):
            return str(value)
        return str(value)
