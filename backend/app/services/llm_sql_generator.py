import json

from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

from app.core.config import settings


class SQLGeneration(BaseModel):
    intent: str = Field(description="Short intent label")
    sql: str = Field(description="Read-only MySQL SELECT statement with named parameters")
    params: dict[str, object] = Field(default_factory=dict, description="SQL named parameters")


class LLMSQLGenerator:
    def __init__(self) -> None:
        self.enabled = bool(settings.openai_api_key and settings.openai_api_key != "replace_with_your_key")
        self.parser = JsonOutputParser(pydantic_object=SQLGeneration)
        self.prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "你是金融数据 NL2SQL 助手，当前系统优先使用你生成 SQL，规则生成器只作为兜底。"
                    "只生成 MySQL SELECT 查询，必须包含 LIMIT，不允许写入、DDL、多语句。"
                    "可用固定表：stocks(id,symbol,name,exchange,industry,listed_date), "
                    "daily_market(stock_id,trade_date,open_price,close_price,high_price,low_price,volume,turnover), "
                    "financial_statements(stock_id,report_period,revenue,net_profit,total_assets,total_liabilities,roe,gross_margin), "
                    "factor_values(stock_id,factor_name,factor_value,trade_date), "
                    "business_metrics(stock_id,metric_name,metric_value,unit,period)。"
                    "这些表和 stocks 关联时使用 stocks.id = 其他表.stock_id。"
                    "如果元数据上下文出现 uploaded_ 开头的用户上传表，也可以查询这些 uploaded_ 表。"
                    "分析类问题也要先生成能支撑分析的数据查询 SQL，不要直接写自然语言分析。"
                    "使用命名参数，例如 :limit、:symbol、:industry。输出必须是 JSON。\n{format_instructions}",
                ),
                (
                    "human",
                    "用户问题：{question}\n返回行数限制：{limit}\n元数据上下文：\n{context}\n请生成 SQL。",
                ),
            ]
        )

    def generate(self, question: str, context: list[dict[str, object]], limit: int) -> tuple[str, str, dict[str, object]] | None:
        if not self.enabled:
            return None
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
                    "question": question,
                    "limit": limit,
                    "context": self._format_context(context),
                    "format_instructions": self.parser.get_format_instructions(),
                }
            )
            intent = str(payload.get("intent", "llm_sql"))
            sql = str(payload["sql"])
            params = dict(payload.get("params") or {})
            params.setdefault("limit", limit)
            return intent, sql, params
        except Exception:
            return None

    def _format_context(self, context: list[dict[str, object]]) -> str:
        items = []
        for item in context[:8]:
            items.append(
                json.dumps(
                    {
                        "object_name": item.get("object_name"),
                        "business_name": item.get("business_name"),
                        "description": item.get("description"),
                        "synonyms": item.get("synonyms"),
                    },
                    ensure_ascii=False,
                )
            )
        return "\n".join(items)
