from __future__ import annotations

import json
from typing import Literal

from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

from app.core.config import settings


RouteName = Literal["data_query", "data_analysis", "general_chat"]


class RouteDecision(BaseModel):
    route: RouteName = Field(description="Intent route")
    rewritten_question: str = Field(description="Self-contained question for downstream tools")
    reason: str = Field(description="Short routing reason")


class LLMIntentRouter:
    def __init__(self) -> None:
        self.enabled = bool(settings.openai_api_key and settings.openai_api_key != "replace_with_your_key")
        self.parser = JsonOutputParser(pydantic_object=RouteDecision)
        self.prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "你是金融数据智能查询系统的意图路由模型。"
                    "根据用户当前输入和短期对话历史选择一个路由："
                    "data_query=需要查询股票/财务/因子/上传CSV等结构化数据；"
                    "data_analysis=需要基于股票数据或查询结果做趋势、对比、原因、总结等分析；"
                    "general_chat=普通闲聊、系统使用说明、与数据查询无关的问题。"
                    "如果用户说“继续分析/它/这家公司”等省略表达，要结合历史改写成自包含问题。"
                    "只输出 JSON。\n{format_instructions}",
                ),
                (
                    "human",
                    "短期历史：\n{history}\n\n当前用户输入：{message}\n请给出路由结果。",
                ),
            ]
        )

    def route(self, message: str, history: list[dict[str, str]]) -> RouteDecision:
        if self.enabled:
            try:
                llm = ChatOpenAI(
                    model=settings.openai_model,
                    api_key=settings.openai_api_key,
                    base_url=settings.openai_base_url or None,
                    temperature=0,
                )
                chain = self.prompt | llm | self.parser
                payload = chain.invoke(
                    {
                        "message": message,
                        "history": self._format_history(history),
                        "format_instructions": self.parser.get_format_instructions(),
                    }
                )
                return RouteDecision.model_validate(payload)
            except Exception:
                return self._fallback_route(message, history)
        return self._fallback_route(message, history)

    def _fallback_route(self, message: str, history: list[dict[str, str]]) -> RouteDecision:
        text = message.lower()
        analysis_keywords = ["分析", "趋势", "原因", "对比", "总结", "怎么看", "评价", "建议", "风险", "表现"]
        data_keywords = [
            "股票",
            "行情",
            "收盘",
            "开盘",
            "成交",
            "市盈率",
            "pe",
            "roe",
            "净利润",
            "营收",
            "财务",
            "因子",
            "排名",
            "最高",
            "最低",
            "查询",
            "csv",
            "数据",
        ]
        if any(keyword in text for keyword in analysis_keywords):
            return RouteDecision(route="data_analysis", rewritten_question=message, reason="fallback: analysis keyword")
        if any(keyword in text for keyword in data_keywords):
            return RouteDecision(route="data_query", rewritten_question=message, reason="fallback: data keyword")
        if history and any(token in text for token in ["继续", "它", "这个", "这家公司", "刚才"]):
            return RouteDecision(route="data_analysis", rewritten_question=message, reason="fallback: follow-up context")
        return RouteDecision(route="general_chat", rewritten_question=message, reason="fallback: general chat")

    def _format_history(self, history: list[dict[str, str]]) -> str:
        recent = history[-8:]
        return "\n".join(
            json.dumps({"role": item["role"], "content": item["content"]}, ensure_ascii=False)
            for item in recent
        )
