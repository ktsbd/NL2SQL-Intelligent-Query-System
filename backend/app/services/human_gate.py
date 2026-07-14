from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ConfirmationDecision:
    required: bool
    reason: str = ""


class HumanApprovalGate:
    broad_keywords = ["全部", "所有", "全量", "导出", "下载", "明细", "大批量", "不限制"]

    def check(self, *, question: str, sql: str, limit: int) -> ConfirmationDecision:
        lowered_sql = sql.lower()
        reasons: list[str] = []
        if limit > 30:
            reasons.append(f"返回行数较大（limit={limit}），需要确认后执行")
        if any(keyword in question for keyword in self.broad_keywords):
            reasons.append("问题包含全量、导出或明细类表达，需要确认查询范围")
        if "uploaded_" in lowered_sql:
            reasons.append("SQL 涉及用户上传数据表，需要确认后访问")
        if len(lowered_sql) > 1200:
            reasons.append("生成 SQL 较复杂，需要确认后执行")
        if not reasons:
            return ConfirmationDecision(required=False)
        return ConfirmationDecision(required=True, reason="；".join(reasons))
