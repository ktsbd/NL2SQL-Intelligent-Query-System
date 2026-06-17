# NL2SQL Intelligent Query System 2.0

English | [中文](#中文)

An end-to-end NL2SQL demo for financial data exploration. It combines FastAPI, LangGraph, SQLAlchemy, MySQL, Qdrant, Elasticsearch, and a React/Vite frontend. Version 2.0 adds a general CSV ingestion workflow: upload any CSV file from the browser, automatically create a MySQL `uploaded_*` table, generate metadata, rebuild retrieval indexes, and query the uploaded dataset with natural language.

## Features

- Natural-language to SQL workflow with LangGraph
- Hybrid metadata retrieval through Qdrant, Elasticsearch, and MySQL fallback
- Read-only SQL validation and repair before execution
- Built-in financial demo schema and seed data
- Browser-based CSV upload and automatic table creation
- Metadata generation for uploaded tables and columns
- Optional OpenAI-powered SQL generation when `OPENAI_API_KEY` is configured
- React query workspace showing workflow steps, retrieved context, generated SQL, and result rows

## Architecture

```text
Frontend CSV upload / query
  -> FastAPI routes
  -> CSV importer or NL2SQL service
  -> MetadataCatalog + uploaded_* MySQL tables
  -> Qdrant / Elasticsearch metadata indexes
  -> LangGraph NL2SQL workflow
  -> Read-only SQL execution
```

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) and [docs/project_file_sequence_hierarchical_v2.svg](docs/project_file_sequence_hierarchical_v2.svg) for a file-level flow diagram.

## Tech Stack

- Backend: FastAPI, SQLAlchemy, LangGraph, LangChain
- Database: MySQL
- Retrieval: Qdrant, Elasticsearch, MySQL fallback
- Frontend: React, Vite, TypeScript
- Optional data source helper: AKShare

## Prerequisites

- Docker Desktop or Docker Engine with Docker Compose
- Python 3.11+
- Node.js 18+

## Quick Start

1. Start infrastructure services.

```bash
docker compose -f infra/docker-compose.yml up -d
```

2. Create and activate a Python virtual environment.

Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

macOS/Linux:

```bash
python -m venv .venv
source .venv/bin/activate
```

3. Install backend dependencies.

```bash
pip install -r backend/requirements.txt
```

4. Create a local environment file.

```bash
cp .env.example .env
```

On Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

5. Initialize demo data and metadata indexes.

```bash
export PYTHONPATH=./backend
python backend/app/db/init_db.py
python -c "from app.services.metadata_indexer import MetadataIndexer; print(MetadataIndexer().rebuild())"
```

On Windows PowerShell:

```powershell
$env:PYTHONPATH="$PWD\backend"
python backend\app\db\init_db.py
python -c "from app.services.metadata_indexer import MetadataIndexer; print(MetadataIndexer().rebuild())"
```

6. Start the backend.

```bash
uvicorn app.main:app --app-dir backend --host 0.0.0.0 --port 8000
```

7. Start the frontend in another terminal.

```bash
cd frontend
npm install
npm run dev
```

Open the frontend URL printed by Vite.

## CSV Upload Workflow

1. Download or prepare a CSV file with a header row.
2. Open the frontend.
3. Use the CSV upload button in the left sidebar.
4. The backend will:
   - decode UTF-8/GBK CSV content,
   - infer MySQL column types,
   - create an `uploaded_*` table,
   - insert rows,
   - write table and column metadata,
   - rebuild Qdrant and Elasticsearch indexes.
5. Ask questions such as:

```text
query akshare_sample_market close_price
查询 akshare_sample_market 数据
```

A small sample file is included at [data_samples/akshare_sample_market.csv](data_samples/akshare_sample_market.csv).

## Optional AKShare Import Helper

The main 2.0 workflow is browser-based CSV upload. The repository also includes a command-line helper for importing one AKShare A-share historical market dataset into the built-in `daily_market` table:

```bash
export PYTHONPATH=./backend
python backend/app/data_importers/akshare_stock_importer.py --symbol 600519 --name 贵州茅台 --industry 食品饮料 --start-date 20240601 --end-date 20240614
python -c "from app.services.metadata_indexer import MetadataIndexer; print(MetadataIndexer().rebuild())"
```

AKShare documentation: <https://akshare.akfamily.xyz/data/stock/stock.html>

## Configuration

Backend configuration is read from `.env`.

| Variable | Description |
| --- | --- |
| `MYSQL_HOST`, `MYSQL_PORT`, `MYSQL_USER`, `MYSQL_PASSWORD`, `MYSQL_DATABASE` | MySQL connection settings |
| `QDRANT_URL` | Qdrant HTTP endpoint |
| `ELASTICSEARCH_URL` | Elasticsearch endpoint |
| `CORS_ORIGINS` | Comma-separated frontend origins |
| `OPENAI_API_KEY` | Optional OpenAI API key |
| `OPENAI_MODEL` | Optional model name for LLM SQL generation |

Frontend configuration can be set in `frontend/.env`:

```text
VITE_API_BASE_URL=http://localhost:8000
```

## Repository Layout

```text
backend/        FastAPI backend, database models, NL2SQL workflow, CSV importer
frontend/       React/Vite frontend
infra/          Docker Compose services
data_samples/   Sample CSV files
docs/           Architecture notes and diagrams
```

## Safety Notes

- Generated SQL is validated as read-only `SELECT`.
- Multiple SQL statements and write/DDL keywords are blocked.
- User-uploaded tables are only queryable when their names start with `uploaded_`.
- This is a demo/research project, not a production-ready financial advisory system.

---

## 中文

一个端到端金融数据 NL2SQL 演示项目。系统结合 FastAPI、LangGraph、SQLAlchemy、MySQL、Qdrant、Elasticsearch 和 React/Vite 前端。2.0 版本新增通用 CSV 导入流程：用户可以在浏览器上传任意带表头的 CSV，后端自动创建 MySQL `uploaded_*` 表、导入数据、生成元数据、重建检索索引，然后通过自然语言查询上传数据。

## 功能特性

- 基于 LangGraph 的自然语言转 SQL 工作流
- Qdrant、Elasticsearch、MySQL fallback 混合元数据检索
- SQL 执行前只读校验和自动修复
- 内置金融 Demo 表结构和样例数据
- 浏览器上传 CSV，后端自动建表
- 自动生成上传表和字段的元数据
- 配置 `OPENAI_API_KEY` 后可启用 LLM SQL 生成
- React 查询工作台展示执行步骤、检索上下文、生成 SQL 和结果表格

## 架构

```text
前端 CSV 上传 / 自然语言查询
  -> FastAPI 路由
  -> CSV 导入器或 NL2SQL 服务
  -> MetadataCatalog + uploaded_* MySQL 表
  -> Qdrant / Elasticsearch 元数据索引
  -> LangGraph NL2SQL 工作流
  -> 只读 SQL 执行
```

文件级流程图见 [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) 和 [docs/project_file_sequence_hierarchical_v2.svg](docs/project_file_sequence_hierarchical_v2.svg)。

## 技术栈

- 后端：FastAPI、SQLAlchemy、LangGraph、LangChain
- 数据库：MySQL
- 检索：Qdrant、Elasticsearch、MySQL fallback
- 前端：React、Vite、TypeScript
- 可选数据源工具：AKShare

## 环境要求

- Docker Desktop 或带 Docker Compose 的 Docker Engine
- Python 3.11+
- Node.js 18+

## 快速启动

1. 启动基础服务。

```bash
docker compose -f infra/docker-compose.yml up -d
```

2. 创建并激活 Python 虚拟环境。

Windows PowerShell：

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

macOS/Linux：

```bash
python -m venv .venv
source .venv/bin/activate
```

3. 安装后端依赖。

```bash
pip install -r backend/requirements.txt
```

4. 创建本地环境配置。

```bash
cp .env.example .env
```

Windows PowerShell：

```powershell
Copy-Item .env.example .env
```

5. 初始化 Demo 数据和元数据索引。

```bash
export PYTHONPATH=./backend
python backend/app/db/init_db.py
python -c "from app.services.metadata_indexer import MetadataIndexer; print(MetadataIndexer().rebuild())"
```

Windows PowerShell：

```powershell
$env:PYTHONPATH="$PWD\backend"
python backend\app\db\init_db.py
python -c "from app.services.metadata_indexer import MetadataIndexer; print(MetadataIndexer().rebuild())"
```

6. 启动后端。

```bash
uvicorn app.main:app --app-dir backend --host 0.0.0.0 --port 8000
```

7. 另开终端启动前端。

```bash
cd frontend
npm install
npm run dev
```

打开 Vite 终端输出的前端访问地址。

## CSV 上传流程

1. 准备一个带表头的 CSV 文件。
2. 打开前端页面。
3. 点击左侧侧边栏的 CSV 上传按钮。
4. 后端会自动完成：
   - 识别 UTF-8/GBK CSV 编码，
   - 推断 MySQL 字段类型，
   - 创建 `uploaded_*` 表，
   - 插入数据行，
   - 写入表和字段元数据，
   - 重建 Qdrant 和 Elasticsearch 索引。
5. 可以测试：

```text
query akshare_sample_market close_price
查询 akshare_sample_market 数据
```

项目内置样例：[data_samples/akshare_sample_market.csv](data_samples/akshare_sample_market.csv)。

## 可选 AKShare 导入工具

2.0 主流程是浏览器上传 CSV。仓库中也保留了一个命令行辅助工具，可把单只 A 股历史行情导入内置 `daily_market` 表：

```bash
export PYTHONPATH=./backend
python backend/app/data_importers/akshare_stock_importer.py --symbol 600519 --name 贵州茅台 --industry 食品饮料 --start-date 20240601 --end-date 20240614
python -c "from app.services.metadata_indexer import MetadataIndexer; print(MetadataIndexer().rebuild())"
```

AKShare 文档：<https://akshare.akfamily.xyz/data/stock/stock.html>

## 配置说明

后端配置从 `.env` 读取。

| 变量 | 说明 |
| --- | --- |
| `MYSQL_HOST`, `MYSQL_PORT`, `MYSQL_USER`, `MYSQL_PASSWORD`, `MYSQL_DATABASE` | MySQL 连接配置 |
| `QDRANT_URL` | Qdrant HTTP 地址 |
| `ELASTICSEARCH_URL` | Elasticsearch 地址 |
| `CORS_ORIGINS` | 前端来源白名单，多个值用逗号分隔 |
| `OPENAI_API_KEY` | 可选 OpenAI API Key |
| `OPENAI_MODEL` | 可选 LLM SQL 生成模型 |

前端可在 `frontend/.env` 中配置：

```text
VITE_API_BASE_URL=http://localhost:8000
```

## 目录结构

```text
backend/        FastAPI 后端、数据库模型、NL2SQL 工作流、CSV 导入器
frontend/       React/Vite 前端
infra/          Docker Compose 服务配置
data_samples/   CSV 样例文件
docs/           架构说明和流程图
```

## 安全说明

- 生成 SQL 会经过只读 `SELECT` 校验。
- 禁止多语句、写入语句和 DDL 关键词。
- 用户上传表只有 `uploaded_` 前缀才允许查询。
- 本项目是 Demo/研究项目，不构成生产级金融建议系统。
