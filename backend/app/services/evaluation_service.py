from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from typing import Any

from app.db.models import EvaluationCaseResult, EvaluationRun
from app.db.session import SessionLocal
from app.services.analysis_planner import AnalysisPlanner
from app.services.nl2sql_service import NL2SQLService


@dataclass(frozen=True)
class EvaluationCase:
    question: str
    expected_sql_contains: list[str] = field(default_factory=list)
    expected_context_contains: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class PlannerEvaluationCase:
    question: str
    expected_tasks: list[str]


DEFAULT_CASES = [
    EvaluationCase(
        question="查询贵州茅台最近行情",
        expected_sql_contains=["daily_market", "stocks", "limit"],
        expected_context_contains=["daily_market"],
    ),
    EvaluationCase(
        question="银行行业ROE最高的公司有哪些",
        expected_sql_contains=["financial_statements", "roe", "stocks"],
        expected_context_contains=["financial_statements"],
    ),
    EvaluationCase(
        question="市盈率最低的股票有哪些",
        expected_sql_contains=["factor_values", "pe_ttm", "stocks"],
        expected_context_contains=["factor_values"],
    ),
    EvaluationCase(
        question="查询我上传的CSV数据",
        expected_sql_contains=["uploaded_"],
        expected_context_contains=["uploaded_"],
    ),
    EvaluationCase(
        question="查询贵州茅台净利润",
        expected_sql_contains=["financial_statements", "net_profit", "stocks"],
        expected_context_contains=["financial_statements"],
    ),
    EvaluationCase(
        question="食品饮料行业有哪些股票",
        expected_sql_contains=["stocks", "industry", "limit"],
        expected_context_contains=["stocks"],
    ),
    EvaluationCase(
        question="动量最高的股票有哪些",
        expected_sql_contains=["factor_values", "momentum_20d", "stocks"],
        expected_context_contains=["factor_values"],
    ),
    EvaluationCase(
        question="动力电池装机量最高的公司有哪些",
        expected_sql_contains=["business_metrics", "stocks"],
        expected_context_contains=["business_metrics"],
    ),
]

PLANNER_CASES = [
    PlannerEvaluationCase(
        question="从行情、估值、财务和风险几个角度分析贵州茅台是否值得关注",
        expected_tasks=["market", "valuation", "financial", "risk"],
    ),
    PlannerEvaluationCase(
        question="全面分析宁德时代的业务指标、财务质量和估值水平",
        expected_tasks=["business", "financial", "valuation"],
    ),
]


class EvaluationService:
    def __init__(self) -> None:
        self.nl2sql = NL2SQLService()
        self.planner = AnalysisPlanner()

    def run_default(self, limit: int = 8) -> dict[str, Any]:
        case_results = []
        passed = 0
        total_latency = 0
        sql_executable = 0
        sql_contains = 0
        context_contains = 0
        retrieval_rounds = 0
        for case in DEFAULT_CASES:
            started = time.perf_counter()
            try:
                result = self.nl2sql.query(case.question, limit=limit, confirmed=True)
                latency_ms = int((time.perf_counter() - started) * 1000)
                total_latency += latency_ms
                checks = self._check_case(case, result)
                case_passed = all(checks.values())
                passed += 1 if case_passed else 0
                sql_executable += 1 if checks.get("sql_executable") else 0
                sql_contains += 1 if checks.get("sql_contains") else 0
                context_contains += 1 if checks.get("context_contains") else 0
                retrieval_rounds += int((result.get("retrieval_diagnostics") or {}).get("rounds", 1))
                case_results.append(
                    {
                        "question": case.question,
                        "passed": case_passed,
                        "latency_ms": latency_ms,
                        "checks": checks,
                        "sql": result.get("sql", ""),
                        "steps": result.get("steps", []),
                    }
                )
            except Exception as exc:
                latency_ms = int((time.perf_counter() - started) * 1000)
                total_latency += latency_ms
                case_results.append(
                    {
                        "question": case.question,
                        "passed": False,
                        "latency_ms": latency_ms,
                        "checks": {"exception": False},
                        "error": str(exc),
                    }
                )

        metrics = {
            "nl2sql_cases": len(DEFAULT_CASES),
            "nl2sql_passed_cases": passed,
            "nl2sql_pass_rate": round(passed / max(len(DEFAULT_CASES), 1), 4),
            "sql_execution_rate": round(sql_executable / max(len(DEFAULT_CASES), 1), 4),
            "sql_semantic_hit_rate": round(sql_contains / max(len(DEFAULT_CASES), 1), 4),
            "context_hit_rate": round(context_contains / max(len(DEFAULT_CASES), 1), 4),
            "avg_retrieval_rounds": round(retrieval_rounds / max(len(DEFAULT_CASES), 1), 2),
            "avg_latency_ms": int(total_latency / max(len(DEFAULT_CASES), 1)),
        }
        planner_metrics, planner_results = self._run_planner_cases()
        metrics.update(planner_metrics)
        case_results.extend(planner_results)
        metrics["total_cases"] = len(case_results)
        metrics["passed_cases"] = sum(1 for item in case_results if item.get("passed"))
        metrics["pass_rate"] = round(metrics["passed_cases"] / max(metrics["total_cases"], 1), 4)
        run_id = self._persist(metrics, case_results)
        return {"run_id": run_id, "metrics": metrics, "cases": case_results}

    def _run_planner_cases(self) -> tuple[dict[str, Any], list[dict[str, Any]]]:
        results = []
        passed = 0
        task_hits = 0
        total_expected = 0
        for case in PLANNER_CASES:
            started = time.perf_counter()
            plan = self.planner.plan(case.question, "data_analysis")
            actual_tasks = [task.name for task in plan.tasks]
            expected = set(case.expected_tasks)
            actual = set(actual_tasks)
            hit_count = len(expected & actual)
            total_expected += len(expected)
            task_hits += hit_count
            case_passed = plan.enabled and expected.issubset(actual)
            passed += 1 if case_passed else 0
            results.append(
                {
                    "question": case.question,
                    "passed": case_passed,
                    "latency_ms": int((time.perf_counter() - started) * 1000),
                    "checks": {
                        "planner_enabled": plan.enabled,
                        "expected_tasks_hit": case_passed,
                    },
                    "planner": {
                        "source": plan.source,
                        "reason": plan.reason,
                        "expected_tasks": case.expected_tasks,
                        "actual_tasks": actual_tasks,
                    },
                }
            )
        return (
            {
                "planner_case_pass_rate": round(passed / max(len(PLANNER_CASES), 1), 4),
                "planner_task_hit_rate": round(task_hits / max(total_expected, 1), 4),
            },
            results,
        )

    def _check_case(self, case: EvaluationCase, result: dict[str, Any]) -> dict[str, bool]:
        sql = f"{result.get('intent', '')} {result.get('sql', '')}".lower()
        context_text = " ".join(str(item.get("object_name", "")) for item in result.get("context", [])).lower()
        rows = result.get("rows", [])
        return {
            "sql_executable": bool(result.get("columns")) or isinstance(rows, list),
            "sql_contains": all(token.lower() in sql for token in case.expected_sql_contains),
            "context_contains": all(token.lower() in context_text for token in case.expected_context_contains),
        }

    def _persist(self, metrics: dict[str, Any], case_results: list[dict[str, Any]]) -> int:
        with SessionLocal() as session:
            run = EvaluationRun(
                name="default_nl2sql_regression",
                total_cases=metrics["total_cases"],
                passed_cases=metrics["passed_cases"],
                metrics_json=json.dumps(metrics, ensure_ascii=False),
            )
            session.add(run)
            session.flush()
            for item in case_results:
                session.add(
                    EvaluationCaseResult(
                        run_id=run.id,
                        question=str(item["question"]),
                        passed=1 if item.get("passed") else 0,
                        expected_json=json.dumps(item.get("checks", {}), ensure_ascii=False),
                        actual_json=json.dumps(item, ensure_ascii=False, default=str),
                        error_message=str(item.get("error", "")),
                        latency_ms=int(item.get("latency_ms", 0)),
                    )
                )
            session.commit()
            return int(run.id)
