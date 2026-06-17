# Architecture / 架构说明

## English

NL2SQL Intelligent Query System 2.0 has two data paths:

1. Built-in financial demo data
   - `backend/app/db/models.py` defines the fixed schema.
   - `backend/app/db/init_db.py` creates tables and seeds sample financial data.
   - `MetadataCatalog` stores table, column, metric, and business-term metadata.

2. User-uploaded CSV data
   - `frontend/src/main.tsx` uploads CSV files through `POST /api/datasets/upload`.
   - `backend/app/api/datasets.py` receives multipart files.
   - `backend/app/services/csv_dataset_importer.py` decodes CSV, infers column types, creates `uploaded_*` tables, inserts rows, and writes metadata.
   - `MetadataIndexer` rebuilds Qdrant and Elasticsearch indexes after upload.

Query path:

```text
User question
  -> /api/nl2sql/stream or /api/nl2sql/query
  -> NL2SQLService
  -> NL2SQLWorkflow
  -> MetadataRetriever
  -> NL2SQLGenerator / LLMSQLGenerator
  -> SQLExecutor
  -> MySQL
  -> JSON/SSE response
```

Important safety boundary:

- `SQLExecutor` only allows `SELECT`.
- Built-in tables are allowlisted.
- User tables must start with `uploaded_`.

## 中文

NL2SQL Intelligent Query System 2.0 有两条数据链路：

1. 内置金融 Demo 数据
   - `backend/app/db/models.py` 定义固定表结构。
   - `backend/app/db/init_db.py` 创建表并插入金融样例数据。
   - `MetadataCatalog` 保存表、字段、指标和业务术语元数据。

2. 用户上传 CSV 数据
   - `frontend/src/main.tsx` 通过 `POST /api/datasets/upload` 上传 CSV。
   - `backend/app/api/datasets.py` 接收 multipart 文件。
   - `backend/app/services/csv_dataset_importer.py` 解码 CSV、推断字段类型、创建 `uploaded_*` 表、插入数据并写入元数据。
   - 上传完成后 `MetadataIndexer` 重建 Qdrant 和 Elasticsearch 索引。

查询链路：

```text
用户问题
  -> /api/nl2sql/stream 或 /api/nl2sql/query
  -> NL2SQLService
  -> NL2SQLWorkflow
  -> MetadataRetriever
  -> NL2SQLGenerator / LLMSQLGenerator
  -> SQLExecutor
  -> MySQL
  -> JSON/SSE 响应
```

重要安全边界：

- `SQLExecutor` 只允许 `SELECT`。
- 内置表使用白名单。
- 用户上传表必须以 `uploaded_` 开头。
