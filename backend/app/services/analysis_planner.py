from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

from app.core.config import settings


TaskName = Literal["market", "valuation", "financial", "risk", "business", "dataset"]


class PlanStepPayload(BaseModel):
    name: TaskName
    question: str = Field(min_length=4, max_length=120)
    goal: str = Field(min_length=2, max_length=120)


class PlanPayload(BaseModel):
    enabled: bool
    reason: str
    tasks: list[PlanStepPayload] = Field(default_factory=list)


@dataclass(frozen=True)
class PlanTask:
    name: str
    question: str
    goal: str
    source: str = "rules"


@dataclass(frozen=True)
class AnalysisPlan:
    enabled: bool
    reason: str
    tasks: list[PlanTask]
    source: str = "rules"


class AnalysisPlanner:
    allowed_tasks = {"market", "valuation", "financial", "risk", "business", "dataset"}
    stock_aliases = ["贵州茅台", "茅台", "平安银行", "宁德时代", "中国平安", "招商银行", "招行", "海康威视"]
    complex_keywords = ["综合", "全面", "多个角度", "几个角度", "从", "是否值得关注", "怎么样", "分析"]

    def __init__(self) -> None:
        self.enabled = bool(settings.openai_api_key and settings.openai_api_key != "replace_with_your_key")
        self.parser = JsonOutputParser(pydantic_object=PlanPayload)
        self.prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "你是金融数据 Agent 的任务规划器。"
                    "你的职责是判断一个分析类问题是否需要拆成多个可执行子任务。"
                    "只允许使用这些子任务 name：market=行情趋势，valuation=估值因子，financial=财务质量，risk=风险波动，business=业务指标，dataset=上传数据画像。"
                    "每个子任务 question 必须是可直接交给 NL2SQL 的中文查询问题。"
                    "如果问题只需要单次查询，enabled=false。"
                    "最多输出 4 个子任务，避免过度规划。"
                    "只输出 JSON。\n{format_instructions}",
                ),
                ("human", "route={route}\n用户问题：{question}\n请规划。"),
            ]
        )

    def plan(self, question: str, route: str) -> AnalysisPlan:
        if route != "data_analysis":
            return AnalysisPlan(enabled=False, reason="route_not_analysis", tasks=[])
        if self.enabled:
            llm_plan = self._llm_plan(question, route)
            if llm_plan and llm_plan.enabled:
                return llm_plan
        return self._rule_plan(question, route)

    def replan_empty_task(self, original_question: str, failed_task: PlanTask) -> PlanTask | None:
        if failed_task.name == "valuation":
            return PlanTask(
                name="valuation",
                question=f"{self._target(original_question)}市盈率最低或估值因子数据",
                goal="放宽估值查询表达，重新获取估值指标",
                source="replan",
            )
        if failed_task.name == "financial":
            return PlanTask(
                name="financial",
                question=f"{self._target(original_question)}净利润 ROE 营收 财务数据",
                goal="放宽财务指标查询表达，重新获取财务数据",
                source="replan",
            )
        if failed_task.name == "market":
            return PlanTask(
                name="market",
                question=f"{self._target(original_question)}行情 收盘价 成交量",
                goal="放宽行情查询表达，重新获取交易数据",
                source="replan",
            )
        return None

    def _llm_plan(self, question: str, route: str) -> AnalysisPlan | None:
        try:
            chain = self.prompt | ChatOpenAI(
                model=settings.openai_model,
                api_key=settings.openai_api_key,
                base_url=settings.openai_base_url or None,
                temperature=0,
            ) | self.parser
            payload = chain.invoke(
                {
                    "route": route,
                    "question": question,
                    "format_instructions": self.parser.get_format_instructions(),
                }
            )
            parsed = PlanPayload.model_validate(payload)
            return self._sanitize_llm_plan(parsed)
        except Exception:
            return None

    def _sanitize_llm_plan(self, payload: PlanPayload) -> AnalysisPlan:
        tasks: list[PlanTask] = []
        seen = set()
        for task in payload.tasks[:4]:
            if task.name not in self.allowed_tasks or task.name in seen:
                continue
            question = task.question.strip()
            goal = task.goal.strip()
            if not question or len(question) > 120:
                continue
            tasks.append(PlanTask(name=task.name, question=question, goal=goal, source="llm"))
            seen.add(task.name)
        return AnalysisPlan(
            enabled=payload.enabled and len(tasks) >= 2,
            reason=payload.reason or "llm_plan",
            tasks=tasks,
            source="llm",
        )

    def _rule_plan(self, question: str, route: str) -> AnalysisPlan:
        dimensions = self._dimensions(question)
        if len(dimensions) < 2 and not any(keyword in question for keyword in self.complex_keywords):
            return AnalysisPlan(enabled=False, reason="single_step_analysis", tasks=[])

        target = self._target(question)
        tasks: list[PlanTask] = []
        for dimension in dimensions or ["market", "valuation", "financial", "risk"]:
            tasks.append(self._task_for_dimension(target, dimension))
        deduped: list[PlanTask] = []
        seen = set()
        for task in tasks:
            if task.name not in seen:
                deduped.append(task)
                seen.add(task.name)
        return AnalysisPlan(enabled=len(deduped) >= 2, reason="multi_dimension_analysis", tasks=deduped[:4])

    def _dimensions(self, question: str) -> list[str]:
        dimensions = []
        if any(token in question for token in ["行情", "走势", "趋势", "价格", "收盘", "涨跌"]):
            dimensions.append("market")
        if any(token.lower() in question.lower() for token in ["估值", "市盈率", "pe", "低估", "高估"]):
            dimensions.append("valuation")
        if any(token.lower() in question.lower() for token in ["财务", "roe", "净利润", "营收", "收入", "毛利率"]):
            dimensions.append("financial")
        if any(token in question for token in ["风险", "波动", "回撤", "稳定"]):
            dimensions.append("risk")
        if any(token in question for token in ["业务", "装机量", "库存周转", "不良率"]):
            dimensions.append("business")
        if any(token.lower() in question.lower() for token in ["上传", "csv", "我的数据", "数据集"]):
            dimensions.append("dataset")
        return dimensions

    def _target(self, question: str) -> str:
        for alias in self.stock_aliases:
            if alias in question:
                return alias
        return question

    def _task_for_dimension(self, target: str, dimension: str) -> PlanTask:
        if dimension == "market":
            return PlanTask(name="market", question=f"查询{target}最近行情", goal="获取近期行情和价格变化")
        if dimension == "valuation":
            return PlanTask(name="valuation", question=f"查询{target}市盈率和估值因子", goal="获取估值相关指标")
        if dimension == "financial":
            return PlanTask(name="financial", question=f"查询{target}财务指标 ROE 净利润 营收", goal="获取财务质量指标")
        if dimension == "business":
            return PlanTask(name="business", question=f"查询{target}业务指标", goal="获取业务经营指标")
        if dimension == "dataset":
            return PlanTask(name="dataset", question=f"查询{target}上传CSV数据画像", goal="获取上传数据集概览")
        return PlanTask(name="risk", question=f"分析{target}最近行情风险和波动", goal="获取风险和波动依据")
