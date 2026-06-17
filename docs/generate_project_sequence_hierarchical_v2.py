from pathlib import Path
import html


OUT = Path("docs/project_file_sequence_hierarchical_v2.svg")
MD = Path("docs/project_file_sequence_hierarchical_v2.md")
W = 2900
H = 5200
LEFT_X = 80
FLOW_X = 245
PANEL_X = 520
PANEL_W = 2250
ROW_H = 86
HEADER_H = 82


def zh(text: str) -> str:
    if not text.isascii():
        return text
    return text.encode("ascii").decode("unicode_escape")


phases = [
    {
        "num": "1",
        "title": zh("\\u73af\\u5883\\u4e0e\\u4f9d\\u8d56\\u542f\\u52a8"),
        "y": 120,
        "color": "#0891b2",
        "goal": zh("\\u5148\\u542f\\u52a8 Docker \\u57fa\\u7840\\u670d\\u52a1\\uff0c\\u518d\\u51c6\\u5907 Python \\u4e0e\\u524d\\u7aef\\u4f9d\\u8d56\\u3002"),
        "files": [
            ("infra/docker-compose.yml", "services: mysql, qdrant, elasticsearch", zh("\\u5b9a\\u4e49 MySQL\\u3001Qdrant\\u3001Elasticsearch \\u4e09\\u4e2a\\u5bb9\\u5668\\u670d\\u52a1\\u3002"), zh("\\u57fa\\u7840\\u670d\\u52a1\\u5728\\u7ebf")),
            ("backend/requirements.txt", "fastapi, sqlalchemy, langgraph, qdrant-client, elasticsearch, akshare, python-multipart", zh("\\u5b89\\u88c5\\u540e\\u7aef\\u4f9d\\u8d56\\uff1b2.0 \\u65b0\\u589e akshare \\u548c CSV \\u6587\\u4ef6\\u4e0a\\u4f20\\u4f9d\\u8d56 python-multipart\\u3002"), zh(".venv \\u53ef\\u8fd0\\u884c\\u540e\\u7aef")),
            (".env / .env.example", "MYSQL_*, QDRANT_URL, ELASTICSEARCH_URL, OPENAI_*", zh("\\u4fdd\\u5b58\\u6570\\u636e\\u5e93\\u3001\\u68c0\\u7d22\\u670d\\u52a1\\u548c\\u53ef\\u9009 LLM \\u914d\\u7f6e\\u3002"), zh("\\u5168\\u5c40\\u914d\\u7f6e\\u53ef\\u8bfb")),
            ("backend/app/core/config.py", "Settings, settings, PROJECT_ROOT, ENV_FILE", zh("\\u7528 Pydantic \\u8bfb\\u53d6 .env\\uff0c\\u751f\\u6210\\u6240\\u6709\\u540e\\u7aef\\u6a21\\u5757\\u5171\\u7528\\u7684 settings\\u3002"), zh("\\u540e\\u7aef\\u914d\\u7f6e\\u7edf\\u4e00")),
            ("frontend/package.json", "scripts: dev, build; dependencies", zh("\\u5b9a\\u4e49 React/Vite/TypeScript \\u524d\\u7aef\\u4f9d\\u8d56\\u548c npm \\u542f\\u52a8\\u811a\\u672c\\u3002"), zh("\\u524d\\u7aef\\u53ef\\u542f\\u52a8")),
        ],
    },
    {
        "num": "2",
        "title": zh("\\u6570\\u636e\\u5e93\\u6a21\\u578b\\u4e0e\\u521d\\u59cb\\u6570\\u636e"),
        "y": 640,
        "color": "#16a34a",
        "goal": zh("\\u5148\\u5b9a\\u4e49\\u8868\\u7c7b\\u548c\\u4f1a\\u8bdd\\uff0c\\u518d\\u521b\\u5efa\\u57fa\\u7840\\u91d1\\u878d Demo \\u6570\\u636e\\u3002"),
        "files": [
            ("backend/app/db/base.py", "Base", zh("\\u5b9a\\u4e49 SQLAlchemy DeclarativeBase\\uff0c\\u6240\\u6709 ORM \\u8868\\u7c7b\\u7684\\u7edf\\u4e00\\u57fa\\u7c7b\\u3002"), zh("\\u8868\\u7c7b\\u53ef\\u88ab\\u6536\\u96c6")),
            ("backend/app/db/models.py", "Stock, DailyMarket, FinancialStatement, FactorValue, BusinessMetric, MetadataCatalog", zh("\\u5b9a\\u4e49\\u80a1\\u7968\\u3001\\u884c\\u60c5\\u3001\\u8d22\\u62a5\\u3001\\u56e0\\u5b50\\u3001\\u4e1a\\u52a1\\u6307\\u6807\\u548c\\u5143\\u6570\\u636e\\u8868\\u3002"), zh("\\u56fa\\u5b9a\\u4e1a\\u52a1\\u8868\\u5b8c\\u6210")),
            ("backend/app/db/session.py", "build_mysql_url, engine, SessionLocal", zh("\\u6839\\u636e settings \\u521b\\u5efa MySQL \\u8fde\\u63a5\\u5f15\\u64ce\\u548c\\u4f1a\\u8bdd\\u5de5\\u5382\\u3002"), zh("\\u4ee3\\u7801\\u53ef\\u8bfb\\u5199 MySQL")),
            ("backend/app/db/init_db.py", "init_schema, seed_data, STOCKS, MARKET_ROWS, METADATA_ROWS", zh("\\u521b\\u5efa\\u8868\\u5e76\\u63d2\\u5165 1.0 \\u57fa\\u7840\\u6837\\u4f8b\\u6570\\u636e\\uff0c\\u5305\\u542b\\u5143\\u6570\\u636e\\u77e5\\u8bc6\\u3002"), zh("\\u57fa\\u7840 Demo \\u53ef\\u67e5")),
            ("backend/app/schemas/nl2sql.py", "NL2SQLRequest, RetrievedContext, NL2SQLResponse", zh("\\u5b9a\\u4e49 NL2SQL \\u67e5\\u8be2\\u63a5\\u53e3\\u7684\\u8bf7\\u6c42\\u548c\\u54cd\\u5e94\\u7ed3\\u6784\\u3002"), zh("API \\u6570\\u636e\\u7ed3\\u6784\\u56fa\\u5b9a")),
        ],
    },
    {
        "num": "3",
        "title": zh("2.0 CSV \\u901a\\u7528\\u5bfc\\u5165\\u5206\\u652f"),
        "y": 1160,
        "color": "#0d9488",
        "goal": zh("\\u7528\\u6237\\u4e0b\\u8f7d\\u4efb\\u610f CSV \\u540e\\uff0c\\u5728\\u524d\\u7aef\\u4e00\\u952e\\u4e0a\\u4f20\\uff0c\\u540e\\u7aef\\u81ea\\u52a8\\u5efa\\u8868\\u3001\\u5165\\u5e93\\u548c\\u751f\\u6210\\u5143\\u6570\\u636e\\u3002"),
        "files": [
            ("frontend/src/main.tsx", "uploadCsv, UploadResult, upload-panel", zh("\\u5de6\\u4fa7\\u4fa7\\u8fb9\\u680f\\u65b0\\u589e CSV \\u4e0a\\u4f20\\u6309\\u94ae\\uff0c\\u628a\\u6587\\u4ef6\\u53d1\\u5230 /api/datasets/upload\\u3002"), zh("\\u7528\\u6237\\u9009\\u62e9 CSV")),
            ("backend/app/api/datasets.py", "upload_dataset, DatasetUploadResponse, ImportedColumn", zh("\\u63a5\\u6536 multipart CSV \\u6587\\u4ef6\\uff0c\\u6821\\u9a8c\\u6269\\u5c55\\u540d\\uff0c\\u8c03\\u7528 CSVDatasetImporter\\u3002"), zh("\\u8fdb\\u5165\\u5bfc\\u5165\\u670d\\u52a1")),
            ("backend/app/services/csv_dataset_importer.py", "CSVDatasetImporter.import_csv, _decode, _build_columns, _infer_type", zh("\\u8bfb\\u53d6 UTF-8/GBK CSV\\uff0c\\u6e05\\u6d17\\u5217\\u540d\\uff0c\\u63a8\\u65ad BIGINT/DECIMAL/DATETIME/VARCHAR/TEXT\\u3002"), zh("\\u5f97\\u5230\\u5efa\\u8868\\u65b9\\u6848")),
            ("backend/app/services/csv_dataset_importer.py", "_create_table, _insert_rows", zh("\\u81ea\\u52a8\\u521b\\u5efa uploaded_* MySQL \\u8868\\uff0c\\u5e76\\u6279\\u91cf\\u63d2\\u5165 CSV \\u884c\\u3002"), zh("\\u4e0a\\u4f20\\u8868\\u5df2\\u5165\\u5e93")),
            ("backend/app/services/csv_dataset_importer.py", "_upsert_metadata, _example_row, _example_values", zh("\\u4e3a\\u4e0a\\u4f20\\u8868\\u548c\\u6bcf\\u4e2a\\u5217\\u5199\\u5165 MetadataCatalog\\uff0c\\u8bb0\\u5f55\\u539f\\u59cb\\u5217\\u540d\\u3001SQL \\u5217\\u540d\\u548c\\u6837\\u4f8b\\u503c\\u3002"), zh("\\u4e0a\\u4f20\\u6570\\u636e\\u53ef\\u88ab\\u68c0\\u7d22")),
            ("data_samples/akshare_sample_market.csv", "sample CSV", zh("\\u672c\\u5730\\u6d4b\\u8bd5\\u6837\\u4f8b\\uff0c\\u6a21\\u62df\\u4ece AKShare \\u6216\\u5176\\u4ed6\\u7ad9\\u70b9\\u4e0b\\u8f7d\\u7684 CSV\\u3002"), zh("\\u53ef\\u7528\\u4e8e\\u9a8c\\u8bc1\\u4e0a\\u4f20")),
        ],
    },
    {
        "num": "4",
        "title": zh("\\u5143\\u6570\\u636e\\u7d22\\u5f15\\u4e0e\\u68c0\\u7d22"),
        "y": 1840,
        "color": "#f97316",
        "goal": zh("\\u628a\\u56fa\\u5b9a\\u8868\\u5143\\u6570\\u636e\\u548c\\u4e0a\\u4f20 CSV \\u8868\\u5143\\u6570\\u636e\\u90fd\\u7d22\\u5f15\\u8d77\\u6765\\uff0c\\u4f9b NL2SQL \\u4f7f\\u7528\\u3002"),
        "files": [
            ("backend/app/services/local_embedding.py", "LocalHashEmbedding, embed, _tokenize", zh("\\u628a\\u5143\\u6570\\u636e\\u6587\\u672c\\u8f6c\\u6210\\u672c\\u5730 128 \\u7ef4\\u54c8\\u5e0c\\u5411\\u91cf\\u3002"), zh("Qdrant \\u53ef\\u5411\\u91cf\\u68c0\\u7d22")),
            ("backend/app/services/metadata_document.py", "MetadataDocument, text, payload, from_model", zh("\\u628a MetadataCatalog \\u884c\\u7edf\\u4e00\\u8f6c\\u4e3a\\u7d22\\u5f15\\u6587\\u6863\\u3002"), zh("\\u7d22\\u5f15\\u6570\\u636e\\u683c\\u5f0f\\u7edf\\u4e00")),
            ("backend/app/services/metadata_indexer.py", "MetadataIndexer.rebuild, _rebuild_qdrant, _rebuild_elasticsearch", zh("\\u91cd\\u5efa Qdrant \\u96c6\\u5408\\u548c Elasticsearch \\u7d22\\u5f15\\uff1bCSV \\u4e0a\\u4f20\\u540e\\u4f1a\\u81ea\\u52a8\\u8c03\\u7528\\u3002"), zh("\\u56fa\\u5b9a\\u8868\\u548c\\u4e0a\\u4f20\\u8868\\u90fd\\u53ef\\u68c0\\u7d22")),
            ("backend/app/services/metadata_retriever.py", "MetadataRetriever.search, _search_qdrant, _search_elasticsearch, _search_database, _merge", zh("\\u5408\\u5e76\\u5411\\u91cf\\u68c0\\u7d22\\u3001\\u5173\\u952e\\u8bcd\\u68c0\\u7d22\\u548c MySQL \\u515c\\u5e95\\u7ed3\\u679c\\u3002"), zh("\\u8fd4\\u56de context")),
            ("backend/app/api/metadata.py", "rebuild_metadata_index, search_metadata", zh("\\u63d0\\u4f9b\\u624b\\u52a8\\u91cd\\u5efa\\u7d22\\u5f15\\u548c\\u641c\\u7d22\\u5143\\u6570\\u636e\\u7684 API\\u3002"), zh("\\u8c03\\u8bd5\\u68c0\\u7d22\\u6548\\u679c")),
        ],
    },
    {
        "num": "5",
        "title": zh("NL2SQL \\u751f\\u6210\\u4e0e uploaded_* \\u67e5\\u8be2"),
        "y": 2400,
        "color": "#7c3aed",
        "goal": zh("\\u5148\\u6839\\u636e\\u95ee\\u9898\\u751f\\u6210\\u9ed8\\u8ba4 SQL\\uff0c\\u518d\\u7528\\u5143\\u6570\\u636e\\u5224\\u65ad\\u662f\\u5426\\u8981\\u67e5\\u4e0a\\u4f20\\u8868\\u3002"),
        "files": [
            ("backend/app/services/nl2sql_generator.py", "generate, generate_uploaded, _pick_uploaded_table, _uploaded_columns", zh("\\u89c4\\u5219 SQL \\u751f\\u6210\\u5668\\uff1b2.0 \\u65b0\\u589e\\u4e0a\\u4f20\\u8868\\u8bc6\\u522b\\u548c uploaded_* SELECT \\u751f\\u6210\\u3002"), zh("\\u65e0 LLM \\u4e5f\\u80fd\\u67e5 CSV")),
            ("backend/app/services/llm_sql_generator.py", "LLMSQLGenerator.generate, _format_context, SQLGeneration", zh("\\u53ef\\u9009 LLM SQL \\u751f\\u6210\\uff1b\\u63d0\\u793a\\u8bcd\\u5df2\\u5141\\u8bb8\\u67e5\\u8be2 uploaded_ \\u5f00\\u5934\\u7684\\u7528\\u6237\\u4e0a\\u4f20\\u8868\\u3002"), zh("\\u6709 Key \\u65f6\\u53ef\\u589e\\u5f3a")),
            ("backend/app/services/sql_executor.py", "validate, repair, execute, ALLOWED_TABLES", zh("\\u53ea\\u5141\\u8bb8 SELECT\\uff0c\\u7981\\u6b62\\u5199\\u5165\\u548c DDL\\uff1b2.0 \\u653e\\u884c uploaded_* \\u8868\\u7684\\u53ea\\u8bfb\\u67e5\\u8be2\\u3002"), zh("\\u67e5\\u8be2\\u5b89\\u5168\\u6267\\u884c")),
            ("backend/app/services/nl2sql_workflow.py", "_parse_intent, _retrieve_context, _generate_sql, _validate_sql, _execute_sql", zh("LangGraph \\u4e3b\\u6d41\\u7a0b\\uff1a\\u89e3\\u6790\\u610f\\u56fe -> \\u68c0\\u7d22\\u4e0a\\u4e0b\\u6587 -> \\u4f18\\u5148\\u751f\\u6210\\u4e0a\\u4f20\\u8868 SQL -> \\u6821\\u9a8c -> \\u6267\\u884c\\u3002"), zh("\\u5b8c\\u6574\\u67e5\\u8be2\\u72b6\\u6001")),
            ("backend/app/services/nl2sql_service.py", "NL2SQLService.query, _context_item", zh("\\u5c01\\u88c5\\u5de5\\u4f5c\\u6d41\\u7ed3\\u679c\\uff0c\\u8f6c\\u6210 API \\u9700\\u8981\\u7684 JSON \\u54cd\\u5e94\\u3002"), zh("\\u524d\\u7aef\\u53ef\\u5c55\\u793a")),
        ],
    },
    {
        "num": "6",
        "title": zh("\\u540e\\u7aef API \\u542f\\u52a8\\u5c42"),
        "y": 2960,
        "color": "#2563eb",
        "goal": zh("\\u628a\\u5065\\u5eb7\\u68c0\\u67e5\\u3001CSV \\u4e0a\\u4f20\\u3001\\u5143\\u6570\\u636e\\u548c NL2SQL \\u90fd\\u6ce8\\u518c\\u6210 HTTP \\u63a5\\u53e3\\u3002"),
        "files": [
            ("backend/app/api/health.py", "health_check", zh("\\u63d0\\u4f9b GET /api/health\\uff0c\\u7528\\u4e8e\\u786e\\u8ba4\\u540e\\u7aef\\u670d\\u52a1\\u6d3b\\u7740\\u3002"), zh("\\u542f\\u52a8\\u68c0\\u67e5")),
            ("backend/app/api/datasets.py", "POST /api/datasets/upload", zh("2.0 \\u65b0\\u589e CSV \\u4e0a\\u4f20\\u5165\\u53e3\\uff0c\\u8fde\\u63a5\\u524d\\u7aef\\u6587\\u4ef6\\u6309\\u94ae\\u548c\\u540e\\u7aef\\u81ea\\u52a8\\u5bfc\\u5165\\u670d\\u52a1\\u3002"), zh("\\u6570\\u636e\\u4e00\\u952e\\u5165\\u5e93")),
            ("backend/app/api/nl2sql.py", "query, stream_query, _sse", zh("\\u63d0\\u4f9b JSON \\u67e5\\u8be2\\u548c SSE \\u6d41\\u5f0f\\u67e5\\u8be2\\uff0c\\u524d\\u7aef\\u4e3b\\u8981\\u8c03\\u7528 stream_query\\u3002"), zh("\\u81ea\\u7136\\u8bed\\u8a00\\u53ef\\u67e5")),
            ("backend/app/main.py", "app, CORS, include_router", zh("\\u521b\\u5efa FastAPI app\\uff0c\\u6ce8\\u518c health/datasets/metadata/nl2sql \\u8def\\u7531\\u548c CORS\\u3002"), zh("app.main:app \\u53ef\\u542f\\u52a8")),
            ("uvicorn app.main:app", "--app-dir backend --host 127.0.0.1 --port 8000", zh("\\u542f\\u52a8\\u540e\\u7aef API \\u670d\\u52a1\\u3002"), zh("8000 \\u7aef\\u53e3\\u5728\\u7ebf")),
        ],
    },
    {
        "num": "7",
        "title": zh("\\u524d\\u7aef\\u4ea4\\u4e92\\u4e0e\\u6700\\u7ec8\\u6f14\\u793a"),
        "y": 3520,
        "color": "#dc2626",
        "goal": zh("\\u7528\\u6237\\u5728\\u7f51\\u9875\\u4e2d\\u4e0a\\u4f20 CSV \\u6216\\u8f93\\u5165\\u95ee\\u9898\\uff0c\\u524d\\u7aef\\u5c55\\u793a SQL\\u3001\\u68c0\\u7d22\\u4e0a\\u4e0b\\u6587\\u548c\\u7ed3\\u679c\\u8868\\u3002"),
        "files": [
            ("frontend/index.html", "root, module script", zh("\\u63d0\\u4f9b React \\u6302\\u8f7d\\u70b9\\u548c Vite \\u5165\\u53e3\\u811a\\u672c\\u3002"), zh("\\u9875\\u9762\\u5bbf\\u4e3b")),
            ("frontend/src/main.tsx", "App, runQuery, handleSseChunk, uploadCsv, Metric", zh("\\u524d\\u7aef\\u4e3b\\u7ec4\\u4ef6\\uff1a\\u53d1\\u8d77 SSE \\u67e5\\u8be2\\u3001\\u89e3\\u6790\\u6d41\\u5f0f\\u4e8b\\u4ef6\\u3001\\u5904\\u7406 CSV \\u4e0a\\u4f20\\u5e76\\u5c55\\u793a\\u7ed3\\u679c\\u3002"), zh("\\u7528\\u6237\\u53ef\\u64cd\\u4f5c")),
            ("frontend/src/styles.css", "app-shell, sidebar, upload-panel, query-bar, result-panel", zh("\\u5b9a\\u4e49\\u4fa7\\u8fb9\\u680f\\u3001CSV \\u4e0a\\u4f20\\u533a\\u3001\\u67e5\\u8be2\\u6761\\u3001SQL \\u9762\\u677f\\u548c\\u7ed3\\u679c\\u8868\\u683c\\u6837\\u5f0f\\u3002"), zh("\\u754c\\u9762\\u5c42\\u6b21\\u6e05\\u6670")),
            ("frontend/src/vite-env.d.ts", "vite/client", zh("\\u8ba9 TypeScript \\u8bc6\\u522b Vite \\u73af\\u5883\\u7c7b\\u578b\\u3002"), zh("\\u7c7b\\u578b\\u68c0\\u67e5\\u6b63\\u5e38")),
            ("npm.cmd run dev", "vite --host 127.0.0.1 --port 5173", zh("\\u542f\\u52a8\\u524d\\u7aef\\u5f00\\u53d1\\u670d\\u52a1\\u3002"), zh("5173 \\u7aef\\u53e3\\u5728\\u7ebf")),
        ],
    },
    {
        "num": "D",
        "title": zh("\\u6587\\u6863\\u3001\\u7248\\u672c\\u5feb\\u7167\\u4e0e\\u53ef\\u9009\\u5de5\\u5177"),
        "y": 4080,
        "color": "#64748b",
        "goal": zh("\\u8fd9\\u4e9b\\u6587\\u4ef6\\u5e2e\\u52a9\\u7406\\u89e3\\u9879\\u76ee\\uff0c\\u6216\\u4f5c\\u4e3a\\u53ef\\u9009\\u6570\\u636e\\u5bfc\\u5165\\u5de5\\u5177\\uff0c\\u4e0d\\u662f\\u524d\\u7aef\\u4e0a\\u4f20\\u4e3b\\u6d41\\u7a0b\\u5fc5\\u9700\\u3002"),
        "files": [
            ("README.md", "Run, Version 2.0 CSV Data Import", zh("\\u8bb0\\u5f55\\u9879\\u76ee\\u542f\\u52a8\\u65b9\\u5f0f\\u3001CSV \\u4e0a\\u4f20\\u7528\\u6cd5\\u548c\\u5f53\\u524d\\u80fd\\u529b\\u3002"), zh("\\u7ed9\\u4eba\\u9605\\u8bfb")),
            ("docs/ARCHITECTURE.md", "architecture notes", zh("\\u7528\\u4e2d\\u82f1\\u6587\\u8bf4\\u660e 2.0 \\u6570\\u636e\\u94fe\\u8def\\u3001CSV \\u4e0a\\u4f20\\u94fe\\u8def\\u548c NL2SQL \\u67e5\\u8be2\\u94fe\\u8def\\u3002"), zh("\\u516c\\u5f00\\u9879\\u76ee\\u6587\\u6863")),
            ("backend/app/data_importers/akshare_stock_importer.py", "import_stock_history, main", zh("\\u53ef\\u9009\\u547d\\u4ee4\\u884c\\u5de5\\u5177\\uff1a\\u76f4\\u63a5\\u4ece AKShare \\u4e0b\\u8f7d\\u5355\\u53ea\\u80a1\\u7968\\u884c\\u60c5\\u5e76\\u5bfc\\u5165 daily_market\\u3002"), zh("\\u975e\\u4e3b\\u6d41 CSV \\u4e0a\\u4f20\\u8def\\u7ebf")),
            ("docs/generate_project_sequence_hierarchical_v2.py", "phases, SVG generation", zh("\\u751f\\u6210\\u5f53\\u524d\\u8fd9\\u5f20 2.0 \\u5206\\u5c42\\u6587\\u4ef6\\u987a\\u5e8f\\u56fe\\u3002"), zh("\\u56fe\\u8868\\u53ef\\u91cd\\u751f\\u6210")),
            (".gitignore", "ignore rules", zh("\\u5ffd\\u7565\\u865a\\u62df\\u73af\\u5883\\u3001node_modules\\u3001dist\\u3001\\u7f13\\u5b58\\u7b49\\u4ea7\\u7269\\u3002"), zh("\\u76ee\\u5f55\\u66f4\\u6e05\\u723d")),
        ],
    },
]

main_flow = [
    ("1", zh("\\u73af\\u5883\\u542f\\u52a8")),
    ("2", zh("\\u5efa\\u57fa\\u7840\\u8868")),
    ("3", zh("CSV \\u4e0a\\u4f20\\u5efa\\u8868")),
    ("4", zh("\\u5143\\u6570\\u636e\\u7d22\\u5f15")),
    ("5", zh("\\u751f\\u6210 SQL")),
    ("6", zh("\\u540e\\u7aef API")),
    ("7", zh("\\u524d\\u7aef\\u4f7f\\u7528")),
]


def esc(value):
    return html.escape(str(value), quote=True)


def wrap_text(text, max_chars):
    lines = []
    current = ""
    for ch in str(text):
        current += ch
        if len(current) >= max_chars or ch in "；;。":
            lines.append(current)
            current = ""
    if current:
        lines.append(current)
    return lines


def text_lines(x, y, text, max_chars, size=14, color="#334155", weight="400", max_lines=3):
    out = []
    for idx, line in enumerate(wrap_text(text, max_chars)[:max_lines]):
        out.append(
            f'<text x="{x}" y="{y + idx * 19}" font-family="Microsoft YaHei, SimHei, Arial" '
            f'font-size="{size}" font-weight="{weight}" fill="{color}">{esc(line)}</text>'
        )
    return "\n".join(out)


def panel_height(count):
    return HEADER_H + 44 + count * ROW_H + 28


def render():
    svg = []
    svg.append(
        f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">
  <defs>
    <marker id="arrow" markerWidth="12" markerHeight="12" refX="10" refY="4" orient="auto" markerUnits="strokeWidth"><path d="M0,0 L0,8 L11,4 z" fill="#1d4ed8"/></marker>
    <filter id="shadow" x="-5%" y="-5%" width="110%" height="110%"><feDropShadow dx="0" dy="2" stdDeviation="2" flood-color="#64748b" flood-opacity="0.14"/></filter>
  </defs>
  <rect width="100%" height="100%" fill="#f8fafc"/>
  <text x="{W/2}" y="48" text-anchor="middle" font-family="Microsoft YaHei, SimHei, Arial" font-size="34" font-weight="700" fill="#0f172a">NL2SQL 2.0 项目文件启动顺序图</text>
  <text x="{W/2}" y="84" text-anchor="middle" font-family="Microsoft YaHei, SimHei, Arial" font-size="17" fill="#475569">2.0 重点新增：浏览器上传 CSV → 自动建 uploaded_* 表 → 自动写元数据 → 重建索引 → 自然语言查询上传表。</text>
'''
    )

    svg.append(f'<rect x="{LEFT_X}" y="120" width="335" height="3840" rx="28" fill="#ffffff" stroke="#cbd5e1" stroke-width="2" filter="url(#shadow)"/>')
    svg.append(f'<text x="{LEFT_X+168}" y="162" text-anchor="middle" font-family="Microsoft YaHei, SimHei, Arial" font-size="22" font-weight="700" fill="#0f172a">主运行路线</text>')
    for idx, (num, label) in enumerate(main_flow):
        y = 235 + idx * 525
        color = phases[idx]["color"]
        svg.append(f'<circle cx="{FLOW_X}" cy="{y}" r="45" fill="{color}"/>')
        svg.append(f'<text x="{FLOW_X}" y="{y-7}" text-anchor="middle" font-family="Arial" font-size="23" font-weight="700" fill="#fff">{esc(num)}</text>')
        svg.append(f'<text x="{FLOW_X}" y="{y+23}" text-anchor="middle" font-family="Microsoft YaHei, SimHei, Arial" font-size="13" fill="#fff">{esc(label)}</text>')
        if idx < len(main_flow) - 1:
            svg.append(f'<line x1="{FLOW_X}" y1="{y+54}" x2="{FLOW_X}" y2="{y+460}" stroke="#1d4ed8" stroke-width="5" marker-end="url(#arrow)"/>')

    for phase in phases:
        y = phase["y"]
        h = panel_height(len(phase["files"]))
        color = phase["color"]
        svg.append(f'<rect x="{PANEL_X}" y="{y}" width="{PANEL_W}" height="{h}" rx="22" fill="#ffffff" stroke="{color}" stroke-width="2.5" filter="url(#shadow)"/>')
        svg.append(f'<rect x="{PANEL_X}" y="{y}" width="{PANEL_W}" height="{HEADER_H}" rx="22" fill="{color}"/>')
        svg.append(f'<text x="{PANEL_X+28}" y="{y+34}" font-family="Microsoft YaHei, SimHei, Arial" font-size="23" font-weight="700" fill="#ffffff">阶段 {esc(phase["num"])}：{esc(phase["title"])}</text>')
        svg.append(f'<text x="{PANEL_X+28}" y="{y+62}" font-family="Microsoft YaHei, SimHei, Arial" font-size="14" fill="#eef2ff">目标：{esc(phase["goal"])}</text>')

        ty = y + HEADER_H
        col_x = [PANEL_X + 18, PANEL_X + 515, PANEL_X + 1120, PANEL_X + 1905]
        headers = [zh("\\u6587\\u4ef6"), zh("\\u5173\\u952e\\u51fd\\u6570 / \\u7c7b / \\u914d\\u7f6e"), zh("\\u8fd9\\u4e2a\\u6587\\u件\\u5e72\\u4ec0\\u4e48"), zh("\\u9636\\u6bb5\\u8f93\\u51fa")]
        svg.append(f'<rect x="{PANEL_X+14}" y="{ty+8}" width="{PANEL_W-28}" height="36" fill="#f1f5f9" stroke="#e2e8f0"/>')
        for i, header in enumerate(headers):
            svg.append(f'<text x="{col_x[i]}" y="{ty+32}" font-family="Microsoft YaHei, SimHei, Arial" font-size="14" font-weight="700" fill="#0f172a">{esc(header)}</text>')

        start_y = ty + 58
        for r, (file, funcs, purpose, output) in enumerate(phase["files"]):
            ry = start_y + r * ROW_H
            fill = "#ffffff" if r % 2 == 0 else "#f8fafc"
            svg.append(f'<rect x="{PANEL_X+14}" y="{ry-24}" width="{PANEL_W-28}" height="{ROW_H}" fill="{fill}" stroke="#e2e8f0"/>')
            svg.append(text_lines(col_x[0], ry, file, 40, size=13, color="#0f172a", weight="700", max_lines=2))
            svg.append(text_lines(col_x[1], ry, funcs, 52, size=12.5, color="#334155", max_lines=3))
            svg.append(text_lines(col_x[2], ry, purpose, 62, size=12.5, color="#334155", max_lines=3))
            svg.append(text_lines(col_x[3], ry, output, 28, size=12.5, color="#334155", max_lines=3))

    for idx, phase in enumerate(phases[:7]):
        y = 235 + idx * 525
        svg.append(f'<line x1="{FLOW_X+50}" y1="{y}" x2="{PANEL_X-18}" y2="{phase["y"]+42}" stroke="{phase["color"]}" stroke-width="3" marker-end="url(#arrow)" opacity="0.6"/>')

    note_y = 4910
    svg.append(f'<rect x="{LEFT_X}" y="{note_y}" width="2690" height="190" rx="18" fill="#0f172a"/>')
    svg.append(f'<text x="{LEFT_X+28}" y="{note_y+32}" font-family="Microsoft YaHei, SimHei, Arial" font-size="18" font-weight="700" fill="#fff">2.0 核心理解：</text>')
    svg.append(f'<text x="{LEFT_X+28}" y="{note_y+64}" font-family="Microsoft YaHei, SimHei, Arial" font-size="15" fill="#dbeafe">1. 固定金融 Demo 表仍然保留：stocks、daily_market、financial_statements、factor_values、business_metrics。</text>')
    svg.append(f'<text x="{LEFT_X+28}" y="{note_y+92}" font-family="Microsoft YaHei, SimHei, Arial" font-size="15" fill="#dbeafe">2. 新增 CSV 主链路：前端上传 CSV，后端自动创建 uploaded_* 表，并把表名、列名、样例值写入 MetadataCatalog。</text>')
    svg.append(f'<text x="{LEFT_X+28}" y="{note_y+120}" font-family="Microsoft YaHei, SimHei, Arial" font-size="15" fill="#dbeafe">3. 查询上传数据时，MetadataRetriever 先召回 uploaded_table / uploaded_column，NL2SQLGenerator.generate_uploaded 再生成 SELECT。</text>')
    svg.append(f'<text x="{LEFT_X+28}" y="{note_y+148}" font-family="Microsoft YaHei, SimHei, Arial" font-size="15" fill="#dbeafe">4. SQLExecutor 仍然只允许 SELECT，并只额外放行 uploaded_ 开头的表，避免上传功能变成任意写库入口。</text>')
    svg.append(f'<text x="{LEFT_X+28}" y="{note_y+176}" font-family="Microsoft YaHei, SimHei, Arial" font-size="15" fill="#dbeafe">5. 可选 AKShare 脚本只是辅助；真正符合 2.0 要求的主入口是浏览器左侧的 CSV 上传按钮。</text>')
    bad_note_ys = {note_y + 32, note_y + 64, note_y + 92, note_y + 120, note_y + 148, note_y + 176}
    svg = [line for line in svg if not any(f'y="{bad_y}"' in line for bad_y in bad_note_ys)]
    notes = [
        zh("2.0 \\u6838\\u5fc3\\u7406\\u89e3\\uff1a"),
        zh("1. \\u56fa\\u5b9a\\u91d1\\u878d Demo \\u8868\\u4ecd\\u7136\\u4fdd\\u7559\\uff1astocks\\u3001daily_market\\u3001financial_statements\\u3001factor_values\\u3001business_metrics\\u3002"),
        zh("2. \\u65b0\\u589e CSV \\u4e3b\\u94fe\\u8def\\uff1a\\u524d\\u7aef\\u4e0a\\u4f20 CSV\\uff0c\\u540e\\u7aef\\u81ea\\u52a8\\u521b\\u5efa uploaded_* \\u8868\\uff0c\\u5e76\\u628a\\u8868\\u540d\\u3001\\u5217\\u540d\\u3001\\u6837\\u4f8b\\u503c\\u5199\\u5165 MetadataCatalog\\u3002"),
        zh("3. \\u67e5\\u8be2\\u4e0a\\u4f20\\u6570\\u636e\\u65f6\\uff0cMetadataRetriever \\u5148\\u53ec\\u56de uploaded_table / uploaded_column\\uff0cNL2SQLGenerator.generate_uploaded \\u518d\\u751f\\u6210 SELECT\\u3002"),
        zh("4. SQLExecutor \\u4ecd\\u7136\\u53ea\\u5141\\u8bb8 SELECT\\uff0c\\u5e76\\u53ea\\u989d\\u5916\\u653e\\u884c uploaded_ \\u5f00\\u5934\\u7684\\u8868\\uff0c\\u907f\\u514d\\u4e0a\\u4f20\\u529f\\u80fd\\u53d8\\u6210\\u4efb\\u610f\\u5199\\u5e93\\u5165\\u53e3\\u3002"),
        zh("5. \\u53ef\\u9009 AKShare \\u811a\\u672c\\u53ea\\u662f\\u8f85\\u52a9\\uff1b\\u771f\\u6b63\\u7b26\\u5408 2.0 \\u8981\\u6c42\\u7684\\u4e3b\\u5165\\u53e3\\u662f\\u6d4f\\u89c8\\u5668\\u5de6\\u4fa7\\u7684 CSV \\u4e0a\\u4f20\\u6309\\u94ae\\u3002"),
    ]
    for index, note in enumerate(notes):
        size = 18 if index == 0 else 15
        weight = "700" if index == 0 else "400"
        fill = "#fff" if index == 0 else "#dbeafe"
        svg.append(f'<text x="{LEFT_X+28}" y="{note_y+32+index*28}" font-family="Microsoft YaHei, SimHei, Arial" font-size="{size}" font-weight="{weight}" fill="{fill}">{esc(note)}</text>')
    svg.append("</svg>")
    OUT.write_text("\n".join(svg), encoding="utf-8")
    MD.write_text(
        zh(
            "# NL2SQL 2.0 \\u9879\\u76ee\\u6587\\u4ef6\\u542f\\u52a8\\u987a\\u5e8f\\u56fe\\n\\n"
            "\\u8fd9\\u5f20\\u56fe\\u4fdd\\u6301 1.0 \\u7684\\u5c42\\u6b21\\u6a21\\u5f0f\\uff0c\\u5e76\\u52a0\\u5165 2.0 \\u7684 CSV \\u901a\\u7528\\u4e0a\\u4f20\\u5bfc\\u5165\\u94fe\\u8def\\u3002\\n\\n"
            "![NL2SQL 2.0 \\u9879\\u76ee\\u6587\\u4ef6\\u542f\\u52a8\\u987a\\u5e8f\\u56fe](project_file_sequence_hierarchical_v2.svg)\\n"
        ),
        encoding="utf-8",
    )
    print(OUT.resolve())
    print(MD.resolve())


if __name__ == "__main__":
    render()
