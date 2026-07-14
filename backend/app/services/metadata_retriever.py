from elasticsearch import Elasticsearch
from qdrant_client import QdrantClient

from app.core.config import settings
from app.db.models import MetadataCatalog
from app.db.session import SessionLocal
from app.services.local_embedding import LocalHashEmbedding
from app.services.metadata_document import from_model
from app.services.metadata_indexer import COLLECTION_NAME, ELASTIC_INDEX_NAME, VECTOR_SIZE


class MetadataRetriever:
    def __init__(self) -> None:
        self.embedding = LocalHashEmbedding(dimension=VECTOR_SIZE)
        self.qdrant = QdrantClient(url=settings.qdrant_url, timeout=5)
        self.elasticsearch = Elasticsearch(settings.elasticsearch_url, request_timeout=5)

    def search(self, query: str, limit: int = 5) -> list[dict[str, object]]:
        results, _ = self.search_with_diagnostics(query, limit)
        return results

    def search_with_diagnostics(self, query: str, limit: int = 5) -> tuple[list[dict[str, object]], dict[str, object]]:
        all_hits: list[tuple[float, list[dict[str, object]]]] = []
        variants = [query]
        rounds = 1

        first_hits = self._search_round(query, limit)
        all_hits.extend(first_hits)
        merged = self._merge(query, all_hits, limit)

        if self._needs_second_round(merged, limit):
            variants.extend(self._query_variants(query))
            rounds = len(variants)
            for variant in variants[1:]:
                all_hits.extend(self._search_round(variant, limit))
            merged = self._merge(query, all_hits, limit)

        diagnostics = {
            "rounds": rounds,
            "variants": variants,
            "top_score": float(merged[0].get("rank_score", 0.0)) if merged else 0.0,
            "returned": len(merged),
        }
        return merged, diagnostics

    def _search_round(self, query: str, limit: int) -> list[tuple[float, list[dict[str, object]]]]:
        vector_hits = self._safe_search(self._search_qdrant, query, limit)
        keyword_hits = self._safe_search(self._search_elasticsearch, query, limit)
        db_hits = self._search_database(query, limit)
        return [(0.50, vector_hits), (0.40, keyword_hits), (0.25, db_hits)]

    def _safe_search(self, search_fn, query: str, limit: int) -> list[dict[str, object]]:
        try:
            return search_fn(query, limit)
        except Exception:
            return []

    def _search_qdrant(self, query: str, limit: int) -> list[dict[str, object]]:
        vector = self.embedding.embed(query)
        hits = self.qdrant.search(
            collection_name=COLLECTION_NAME,
            query_vector=vector,
            limit=limit,
            with_payload=True,
        )
        return [
            {
                "id": hit.id,
                "score": float(hit.score),
                "source": "qdrant",
                **(hit.payload or {}),
            }
            for hit in hits
        ]

    def _search_elasticsearch(self, query: str, limit: int) -> list[dict[str, object]]:
        if not self.elasticsearch.indices.exists(index=ELASTIC_INDEX_NAME):
            return []
        response = self.elasticsearch.search(
            index=ELASTIC_INDEX_NAME,
            size=limit,
            query={
                "multi_match": {
                    "query": query,
                    "fields": ["business_name^3", "object_name^2", "description", "synonyms^2", "example_values"],
                }
            },
        )
        hits = response.get("hits", {}).get("hits", [])
        return [
            {
                "id": int(hit["_id"]),
                "score": float(hit["_score"]),
                "source": "elasticsearch",
                **hit["_source"],
            }
            for hit in hits
        ]

    def _search_database(self, query: str, limit: int) -> list[dict[str, object]]:
        tokens = [token for token in self.embedding._tokenize(query) if len(token) >= 2]
        if not tokens:
            return []
        with SessionLocal() as session:
            rows = session.query(MetadataCatalog).order_by(MetadataCatalog.id).all()
            documents = [from_model(row) for row in rows]
        scored = []
        for document in documents:
            text = document.text.lower()
            score = sum(1 for token in tokens if token.lower() in text)
            if score:
                scored.append({"score": float(score), "source": "mysql", **document.payload()})
        scored.sort(key=lambda item: float(item["score"]), reverse=True)
        return scored[:limit]

    def _merge(self, query: str, weighted_hits: list[tuple[float, list[dict[str, object]]]], limit: int) -> list[dict[str, object]]:
        merged: dict[int, dict[str, object]] = {}
        for weight, hits in weighted_hits:
            for rank, hit in enumerate(hits):
                item_id = int(hit["id"])
                score = (
                    weight * (1.0 / (rank + 1))
                    + self._lexical_bonus(str(hit.get("text", "")), query)
                    + self._domain_bonus(str(hit.get("object_name", "")), query)
                )
                if item_id not in merged:
                    merged[item_id] = {**hit, "sources": [hit["source"]], "rank_score": score}
                else:
                    merged[item_id]["rank_score"] = float(merged[item_id]["rank_score"]) + score
                    sources = set(merged[item_id]["sources"])
                    sources.add(str(hit["source"]))
                    merged[item_id]["sources"] = sorted(sources)

        return sorted(merged.values(), key=lambda item: float(item["rank_score"]), reverse=True)[:limit]

    def _needs_second_round(self, merged: list[dict[str, object]], limit: int) -> bool:
        if len(merged) < min(3, limit):
            return True
        return float(merged[0].get("rank_score", 0.0)) < 0.7

    def _query_variants(self, query: str) -> list[str]:
        expansions = {
            "行情": "日行情 收盘价 开盘价 成交量 成交额 daily_market",
            "价格": "收盘价 开盘价 最高价 最低价 daily_market",
            "财务": "财务报表 净利润 营收 ROE financial_statements",
            "利润": "净利润 财务报表 financial_statements",
            "收入": "营收 revenue financial_statements",
            "估值": "市盈率 pe_ttm 因子 factor_values",
            "市盈率": "PE pe_ttm 估值 因子 factor_values",
            "趋势": "行情 收盘价 动量 momentum_20d factor_values",
            "上传": "CSV uploaded_table uploaded_column 用户上传数据",
            "CSV": "uploaded_table uploaded_column 用户上传数据",
        }
        variants = []
        for keyword, expansion in expansions.items():
            if keyword.lower() in query.lower():
                variants.append(f"{query} {expansion}")
        return variants[:2]

    def _lexical_bonus(self, text: str, query: str) -> float:
        if not query:
            return 0.0
        normalized_text = text.lower()
        tokens = set(self.embedding._tokenize(query))
        if not tokens:
            return 0.0
        matches = sum(1 for token in tokens if len(token) >= 2 and token in normalized_text)
        return min(matches / max(len(tokens), 1), 1.0) * 0.35

    def _domain_bonus(self, object_name: str, query: str) -> float:
        lowered = query.lower()
        domain_keywords = {
            "financial_statements": ["净利润", "roe", "毛利率", "收入", "营收", "资产", "负债", "财务", "利润"],
            "daily_market": ["收盘价", "开盘价", "最高价", "最低价", "成交量", "成交额", "行情", "价格"],
            "factor_values": ["pe", "市盈率", "估值", "因子", "动量", "momentum"],
            "business_metrics": ["装机量", "不良贷款率", "不良率", "库存周转", "业务指标", "经营指标"],
            "stocks": ["股票代码", "上市日期", "交易所", "行业", "公司", "股票"],
        }
        keywords = domain_keywords.get(object_name, [])
        return 0.5 if any(keyword.lower() in lowered for keyword in keywords) else 0.0
