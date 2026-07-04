# Financial Data Agent Query System

English | [中文](#中文)

An end-to-end financial data Agent system for natural-language data query and analysis. The project combines FastAPI, LangGraph, LangChain, SQLAlchemy, MySQL, Qdrant, Elasticsearch, React, TypeScript, and Docker Compose.

The system supports multi-turn chat, LLM-based intent routing, LLM-first NL2SQL generation, read-only SQL validation, RAG metadata retrieval, CSV ingestion, and a configurable Skill/Tool extension layer for financial analysis.

## Features

- Chat-style financial data Agent UI
- Multi-turn short-term memory based on `session_id`
- LLM intent routing: `data_query`, `data_analysis`, `general_chat`
- LLM-first SQL generation with rule-based fallback
- Hybrid metadata retrieval with Qdrant, Elasticsearch, and MySQL fallback
- Read-only SQL validation and automatic `LIMIT` repair
- Natural-language analysis based on SQL results
- General CSV upload with automatic table creation and metadata indexing
- Skill/Tool extension system under `agent_extensions/`
- Default tools for valuation, trend, risk, and dataset profiling

## Architecture

```text
React chat frontend
  -> FastAPI /api/chat
  -> short-term chat memory
  -> LLM intent router
  -> metadata retrieval: Qdrant + Elasticsearch + MySQL fallback
  -> LLM-first SQL generation
  -> read-only SQL validation and repair
  -> SQLAlchemy execution on MySQL
  -> Skill/Tool result analysis
  -> natural-language answer
```

CSV ingestion flow:

```text
CSV upload
  -> encoding detection and header cleanup
  -> MySQL type inference
  -> uploaded_* table creation
  -> batch insert
  -> MetadataCatalog update
  -> Qdrant / Elasticsearch index rebuild
  -> natural-language query and Tool analysis
```

## Tech Stack

- Backend: FastAPI, LangGraph, LangChain, SQLAlchemy
- LLM: OpenAI-compatible chat completion API
- Database: MySQL
- Retrieval: Qdrant, Elasticsearch, MySQL fallback
- Frontend: React, TypeScript, Vite
- Infrastructure: Docker Compose
- Optional data helper: AKShare

## Built-in Skills and Tools

Skills are configured in `agent_extensions/skills/`.

| Skill | Purpose |
| --- | --- |
| `trend_analysis` | Matches trend, price, moving average, volatility, and market-performance questions |
| `valuation_analysis` | Matches PE, valuation, ROE, financial metric, ranking, highest/lowest questions |
| `dataset_profile` | Matches CSV, uploaded dataset, fields, distribution, missing-value, and profiling questions |

Tools are configured in `agent_extensions/tools/`.

| Tool | Purpose |
| --- | --- |
| `moving_average_trend` | Computes latest value, interval change, MA5/MA10, and short-term trend |
| `return_risk_summary` | Computes interval return, volatility, maximum drawdown, min, and max |
| `valuation_snapshot` | Computes average, min, max, and ranking summary for valuation/financial metrics |
| `dataset_profile` | Computes row count, column count, missing values, numeric ranges, and sample fields |

To add a new configuration-only skill, add a JSON file under `agent_extensions/skills/` and reference existing tool names. To add a new executable tool, implement and register a Python function in `backend/app/services/skill_tool_manager.py`, then add its JSON metadata under `agent_extensions/tools/`.

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

Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

5. Initialize demo data and metadata indexes.

```bash
export PYTHONPATH=./backend
python backend/app/db/init_db.py
python -c "from app.services.metadata_indexer import MetadataIndexer; print(MetadataIndexer().rebuild())"
```

Windows PowerShell:

```powershell
$env:PYTHONPATH="$PWD\backend"
python backend\app\db\init_db.py
python -c "from app.services.metadata_indexer import MetadataIndexer; print(MetadataIndexer().rebuild())"
```

6. Start the backend.

```bash
uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000
```

7. Start the frontend in another terminal.

```bash
cd frontend
npm install
npm run dev
```

Open:

```text
http://127.0.0.1:5173
```

## Configuration

Backend configuration is read from `.env`.

| Variable | Description |
| --- | --- |
| `MYSQL_HOST`, `MYSQL_PORT`, `MYSQL_USER`, `MYSQL_PASSWORD`, `MYSQL_DATABASE` | MySQL connection settings |
| `QDRANT_URL` | Qdrant HTTP endpoint |
| `ELASTICSEARCH_URL` | Elasticsearch endpoint |
| `CORS_ORIGINS` | Comma-separated frontend origins |
| `OPENAI_API_KEY` | OpenAI-compatible API key |
| `OPENAI_MODEL` | Chat model name |
| `OPENAI_BASE_URL` | Optional OpenAI-compatible base URL |

Example for Zhipu/OpenAI-compatible API:

```env
OPENAI_MODEL=glm-5.2
OPENAI_BASE_URL=https://open.bigmodel.cn/api/paas/v4/
```

Do not commit `.env`.

Frontend configuration can be set in `frontend/.env`:

```text
VITE_API_BASE_URL=http://localhost:8000
```

## API Overview

| Endpoint | Description |
| --- | --- |
| `POST /api/chat/message` | Chat request with full JSON response |
| `POST /api/chat/stream` | SSE chat stream for frontend |
| `DELETE /api/chat/sessions/{session_id}` | Clear short-term memory |
| `POST /api/nl2sql/query` | Compatibility NL2SQL JSON query |
| `POST /api/nl2sql/stream` | Compatibility NL2SQL SSE query |
| `POST /api/datasets/upload` | Upload CSV and rebuild indexes |
| `GET /api/metadata/search` | Search metadata |
| `POST /api/metadata/index` | Rebuild metadata indexes |
| `GET /api/extensions` | List loaded Skills and Tools |

## Example Questions

```text
Which stocks have the lowest PE ratio?
Analyze the valuation of the stocks with the lowest PE ratios.
Analyze the recent closing-price trend and volatility of Kweichow Moutai.
Query my uploaded CSV dataset.
Summarize the previous result.
```

## Repository Layout

```text
agent_extensions/   Skill and Tool JSON definitions
backend/            FastAPI backend, Agent workflow, database models, CSV importer
frontend/           React/Vite chat frontend
infra/              Docker Compose services
data_samples/       Sample CSV files
docs/               Architecture notes and diagrams
```

## Safety Notes

- Generated SQL is validated as read-only `SELECT`.
- Multiple SQL statements and write/DDL keywords are blocked.
- SQL without `LIMIT` is repaired automatically.
- Uploaded user tables must use the `uploaded_` prefix.
- This project is a demo/research system and does not provide financial advice.

---

## 中文

一个端到端的金融数据 Agent 智能查询与分析系统。项目结合 FastAPI、LangGraph、LangChain、SQLAlchemy、MySQL、Qdrant、Elasticsearch、React、TypeScript 和 Docker Compose。

系统支持多轮自然语言聊天、大模型意图路由、大模型优先 SQL 生成、只读 SQL 安全校验、RAG 元数据召回、CSV 数据接入，以及可配置的 Skill/Tool 金融分析扩展机制。

## 功能特性

- 聊天式金融数据 Agent 前端
- 基于 `session_id` 的短期多轮记忆
- 大模型意图路由：`data_query`、`data_analysis`、`general_chat`
- 大模型优先生成 SQL，规则生成兜底
- Qdrant、Elasticsearch、MySQL fallback 混合元数据召回
- 只读 SQL 校验和缺失 `LIMIT` 自动修复
- 基于 SQL 查询结果生成自然语言分析
- 通用 CSV 上传、自动建表和索引重建
- `agent_extensions/` Skill/Tool 扩展系统
- 内置估值、趋势、风险、数据画像分析工具

## 架构流程

```text
React 聊天前端
  -> FastAPI /api/chat
  -> 短期对话记忆
  -> 大模型意图路由
  -> 元数据召回：Qdrant + Elasticsearch + MySQL fallback
  -> 大模型优先 SQL 生成
  -> 只读 SQL 校验和修复
  -> SQLAlchemy 执行 MySQL 查询
  -> Skill/Tool 工具分析
  -> 自然语言回答
```

CSV 接入流程：

```text
CSV 上传
  -> 编码识别和表头清洗
  -> MySQL 字段类型推断
  -> uploaded_* 动态建表
  -> 批量写入
  -> MetadataCatalog 更新
  -> Qdrant / Elasticsearch 索引重建
  -> 自然语言查询和 Tool 分析
```

## 技术栈

- 后端：FastAPI、LangGraph、LangChain、SQLAlchemy
- 大模型：OpenAI-compatible Chat Completion API
- 数据库：MySQL
- 检索：Qdrant、Elasticsearch、MySQL fallback
- 前端：React、TypeScript、Vite
- 基础设施：Docker Compose
- 可选数据工具：AKShare

## 内置 Skill 和 Tool

Skill 位于 `agent_extensions/skills/`。

| Skill | 用途 |
| --- | --- |
| `trend_analysis` | 匹配趋势、走势、收盘价、均线、波动、行情表现类问题 |
| `valuation_analysis` | 匹配市盈率、估值、ROE、财务指标、排名、最高/最低类问题 |
| `dataset_profile` | 匹配 CSV、上传数据、字段、分布、缺失值、数据画像类问题 |

Tool 位于 `agent_extensions/tools/`。

| Tool | 用途 |
| --- | --- |
| `moving_average_trend` | 计算最新值、区间变化、MA5/MA10 和短期趋势 |
| `return_risk_summary` | 计算区间收益、波动率、最大回撤、最小值和最大值 |
| `valuation_snapshot` | 计算估值/财务指标的均值、最低值、最高值和排名摘要 |
| `dataset_profile` | 统计行数、列数、空值、数值字段范围和示例字段 |

如果只复用已有工具函数，新增 Skill 时只需要在 `agent_extensions/skills/` 添加 JSON 文件并引用已有 tool 名称。如果要新增真正可执行的 Tool，需要在 `backend/app/services/skill_tool_manager.py` 中实现并注册 Python 函数，再在 `agent_extensions/tools/` 添加 JSON 元数据。

## 环境要求

- Docker Desktop 或支持 Docker Compose 的 Docker Engine
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

4. 创建本地环境文件。

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
uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000
```

7. 另开终端启动前端。

```bash
cd frontend
npm install
npm run dev
```

打开：

```text
http://127.0.0.1:5173
```

## 配置说明

后端配置从 `.env` 读取。

| 变量 | 说明 |
| --- | --- |
| `MYSQL_HOST`, `MYSQL_PORT`, `MYSQL_USER`, `MYSQL_PASSWORD`, `MYSQL_DATABASE` | MySQL 连接配置 |
| `QDRANT_URL` | Qdrant HTTP 地址 |
| `ELASTICSEARCH_URL` | Elasticsearch 地址 |
| `CORS_ORIGINS` | 前端来源白名单，多个值用逗号分隔 |
| `OPENAI_API_KEY` | OpenAI-compatible API Key |
| `OPENAI_MODEL` | 聊天模型名称 |
| `OPENAI_BASE_URL` | 可选 OpenAI-compatible Base URL |

智谱等 OpenAI-compatible API 示例：

```env
OPENAI_MODEL=glm-5.2
OPENAI_BASE_URL=https://open.bigmodel.cn/api/paas/v4/
```

不要提交 `.env`。

前端可在 `frontend/.env` 中配置：

```text
VITE_API_BASE_URL=http://localhost:8000
```

## API 概览

| 接口 | 说明 |
| --- | --- |
| `POST /api/chat/message` | 聊天请求，返回完整 JSON |
| `POST /api/chat/stream` | 前端使用的 SSE 聊天流 |
| `DELETE /api/chat/sessions/{session_id}` | 清空短期记忆 |
| `POST /api/nl2sql/query` | 兼容旧版 NL2SQL JSON 查询 |
| `POST /api/nl2sql/stream` | 兼容旧版 NL2SQL SSE 查询 |
| `POST /api/datasets/upload` | 上传 CSV 并重建索引 |
| `GET /api/metadata/search` | 搜索元数据 |
| `POST /api/metadata/index` | 重建元数据索引 |
| `GET /api/extensions` | 查看已加载的 Skill 和 Tool |

## 示例问题

```text
市盈率最低的股票有哪些？
分析市盈率最低的股票估值情况
分析贵州茅台近期收盘价趋势和波动
查询我上传的 CSV 数据
总结刚才的查询结果
```

## 目录结构

```text
agent_extensions/   Skill 和 Tool JSON 定义
backend/            FastAPI 后端、Agent 工作流、数据库模型、CSV 导入器
frontend/           React/Vite 聊天前端
infra/              Docker Compose 服务配置
data_samples/       CSV 示例文件
docs/               架构说明和流程图
```

## 安全说明

- 生成 SQL 会经过只读 `SELECT` 校验。
- 禁止多语句、写入语句和 DDL 关键词。
- 缺失 `LIMIT` 的 SQL 会自动修复。
- 用户上传表必须使用 `uploaded_` 前缀。
- 本项目是 Demo/研究项目，不构成金融投资建议。
