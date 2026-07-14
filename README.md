# Financial Data Agent Query and Analysis System

[中文说明](#中文说明) | [English](#english)

An engineering-oriented financial data Agent system for natural-language querying, NL2SQL generation, multi-step analysis, CSV ingestion, tool-based analytics, observability, and automated evaluation.

The project is built with FastAPI, LangGraph, LangChain, SQLAlchemy, MySQL, Qdrant, Elasticsearch, React, TypeScript, and Docker Compose. It is designed to demonstrate a complete backend Agent application rather than a simple prompt demo.

## 中文说明

### 项目简介

本项目是一个金融数据 Agent 智能查询与分析系统。用户可以通过聊天界面输入自然语言问题，系统会自动判断问题意图，检索金融元数据，生成并校验 SQL，执行查询，并结合工具分析结果返回自然语言回答。

系统支持股票基础数据、行情数据、财务指标、因子指标、业务指标以及用户上传的 CSV 数据。对于复杂分析类问题，系统会先拆解任务，再分别执行行情、估值、财务、风险、业务或数据集分析，最后合并成结构化回答。

### 核心能力

- 聊天式金融数据查询与分析页面。
- 基于大模型的意图路由，规则路由作为兜底。
- 多轮对话问题改写，支持结合历史上下文理解追问。
- 大模型优先生成 SQL，规则 SQL 生成作为兜底机制。
- 基于 LangGraph 编排意图解析、元数据检索、SQL 生成、SQL 校验、SQL 修复和 SQL 执行。
- 融合 Qdrant、Elasticsearch 和 MySQL fallback 的金融元数据混合检索。
- 支持多步 Planner，将复杂分析问题拆成行情、估值、财务、风险、业务、数据集等子任务。
- 子任务查询结果为空时支持 Replan 重试。
- 支持 Skill/Tool 扩展机制，可挂载金融分析工具。
- 支持上传任意带表头 CSV，自动识别编码、清洗字段名、推断字段类型、创建 uploaded_* 表并写入元数据索引。
- SQL 只读安全校验，限制危险关键字、多语句、系统库访问、超大 LIMIT 等风险。
- 对高风险查询、上传表访问、复杂 SQL 等场景支持 Human-in-the-loop 人工确认。
- 支持会话持久化和短期记忆。
- 支持 Trace 日志，记录请求、节点、模型调用、工具调用和异常信息。
- 支持自动化评测 NL2SQL 与 Planner 效果。
- 支持后台任务系统，用于异步执行评测等长任务。

### 架构流程

```text
React + TypeScript 聊天前端
  -> FastAPI Chat API / SSE 流式响应
  -> 会话记忆与历史上下文
  -> 大模型意图路由与问题改写
  -> 复杂问题进入 Planner 拆解
  -> 金融元数据 RAG 检索
       -> Qdrant 向量检索
       -> Elasticsearch 关键词检索
       -> MySQL fallback
  -> 大模型优先生成 SQL
  -> SQL 安全校验 / 自动修复 / 人工确认
  -> SQLAlchemy 执行 MySQL 查询
  -> Skill / Tool 分析查询结果
  -> 大模型生成自然语言回答
  -> Trace / Evaluation / Task 记录
```

CSV 数据接入流程：

```text
CSV 上传
  -> 编码识别
  -> 表头清洗
  -> MySQL 字段类型推断
  -> 创建 uploaded_* 动态表
  -> 批量写入数据
  -> 写入 MetadataCatalog
  -> 重建 Qdrant / Elasticsearch 索引
  -> 支持自然语言查询
```

复杂分析流程：

```text
复杂分析问题
  -> 大模型 Planner 或规则 Planner
  -> 校验计划任务
  -> 子任务 NL2SQL 查询
  -> 空结果 Replan 重试
  -> Skill / Tool 分析每个子任务
  -> 生成综合分析回答
```

### 技术栈

| 层级 | 技术 |
| --- | --- |
| 后端 | FastAPI, LangGraph, LangChain, SQLAlchemy |
| 大模型 | OpenAI-compatible Chat Completion API |
| 数据库 | MySQL |
| 检索 | Qdrant, Elasticsearch, MySQL fallback |
| 前端 | React, TypeScript, Vite |
| 工程化 | Docker Compose, Pydantic, SSE |
| 可观测性 | Trace 表、节点事件、执行耗时、错误记录 |
| 评测 | NL2SQL 用例、Planner 用例、自动评分 |

### 目录结构

```text
backend/
  app/
    api/                 FastAPI 路由
    core/                配置与基础组件
    db/                  SQLAlchemy 模型、数据库初始化、运行时表结构补齐
    schemas/             请求和响应结构
    services/            Agent、NL2SQL、检索、评测、工具、记忆等核心服务
agent_extensions/
  skills/                Skill 定义目录
  tools/                 Tool 实现目录
frontend/
  src/                   React 前端页面
infra/
  docker-compose.yml     MySQL、Qdrant、Elasticsearch 等基础设施
data_samples/            示例数据
docs/                    项目文档和流程图
```

### 环境要求

- Python 3.10+
- Node.js 18+
- Docker Desktop
- Git

### 配置环境变量

首次运行时复制环境变量模板：

```powershell
Copy-Item .env.example .env
```

然后编辑 `.env`，配置自己的大模型服务：

```env
LLM_API_KEY=your-api-key
LLM_BASE_URL=https://your-openai-compatible-endpoint/v1
LLM_MODEL=your-model-name
```

说明：

- `.env` 包含私密信息，不应该提交到 GitHub。
- 当前项目通过 OpenAI-compatible 协议调用大模型，只要服务兼容 `/chat/completions` 风格接口即可接入。

### 启动顺序

1. 启动 Docker Desktop。

2. 启动基础设施：

```powershell
docker compose -f infra\docker-compose.yml up -d
```

3. 激活 Python 虚拟环境：

```powershell
.\.venv\Scripts\Activate.ps1
```

如果是首次拉取项目，需要先安装后端依赖：

```powershell
pip install -r backend\requirements.txt
```

4. 初始化数据库表：

```powershell
$env:PYTHONPATH="$PWD\backend"
python backend\app\db\init_db.py
```

5. 重建元数据索引：

```powershell
$env:PYTHONPATH="$PWD\backend"
python -c "from app.services.metadata_indexer import MetadataIndexer; print(MetadataIndexer().rebuild())"
```

6. 启动后端服务：

```powershell
$env:PYTHONPATH="$PWD\backend"
.\.venv\Scripts\uvicorn.exe app.main:app --app-dir backend --host 127.0.0.1 --port 8000
```

7. 启动前端服务：

```powershell
cd frontend
npm install
npm run dev
```

8. 打开浏览器访问：

```text
http://127.0.0.1:5173
```

### 常用接口

| 接口 | 说明 |
| --- | --- |
| `POST /api/chat/message` | 聊天式 Agent 查询 |
| `GET /api/chat/stream` | SSE 流式响应 |
| `POST /api/nl2sql/query` | NL2SQL 查询 |
| `POST /api/datasets/upload` | 上传 CSV 并导入数据库 |
| `GET /api/metadata/search` | 搜索元数据 |
| `POST /api/metadata/index` | 重建元数据索引 |
| `GET /api/extensions` | 查看 Skill/Tool 扩展 |
| `GET /api/traces` | 查看请求 Trace |
| `GET /api/traces/{trace_id}` | 查看 Trace 节点事件 |
| `POST /api/evaluation/run` | 同步运行自动化评测 |
| `POST /api/evaluation/run-async` | 异步运行自动化评测 |
| `GET /api/tasks/{task_id}` | 查询后台任务状态 |

### GitHub 提交建议

建议提交源码、配置模板、文档和示例数据，不要提交本地运行产物。

应该提交：

```text
README.md
.gitignore
.env.example
backend/
frontend/src/
frontend/package.json
frontend/package-lock.json
infra/
agent_extensions/
data_samples/
docs/
```

不要提交：

```text
.env
.venv/
.runtime/
frontend/node_modules/
frontend/dist/
versions/
tmp/
github_url.txt
__pycache__/
*.pyc
```

推荐更新仓库命令：

```powershell
git status
git add README.md .gitignore .env.example backend frontend agent_extensions infra data_samples docs
git status
git commit -m "Enhance financial data agent system"
git push origin main
```

### 评测与验证

后端代码编译检查：

```powershell
.\.venv\Scripts\python.exe -m compileall backend\app
```

前端构建检查：

```powershell
cd frontend
npm run build
```

运行自动化评测：

```powershell
curl -X POST http://127.0.0.1:8000/api/evaluation/run
```

评测会覆盖 NL2SQL 查询、SQL 执行、语义命中、上下文召回、Planner 任务拆解等指标。

### 安全设计

- 仅允许 SELECT 查询。
- 拦截 INSERT、UPDATE、DELETE、DROP、ALTER、TRUNCATE、CREATE 等写入或 DDL 操作。
- 拦截多语句、SQL 注释、UNION、系统库访问、文件读写等风险。
- 自动限制 LIMIT，避免一次性返回过多数据。
- 对上传表访问、高 LIMIT、复杂 SQL 等场景触发人工确认。
- API Key 只通过环境变量读取，不写入源码。

## English

### Overview

This project is a financial data Agent system for natural-language querying and analysis. A user can ask questions in a chat UI, and the backend routes intent, retrieves metadata, generates SQL, validates and executes the query, calls analysis tools, and returns a natural-language answer.

The system supports built-in stock data, market data, financial metrics, factor metrics, business metrics, and user-uploaded CSV datasets. For complex analysis questions, it can plan subtasks across market, valuation, financial, risk, business, and dataset dimensions.

### Features

- Chat-style financial data query and analysis UI.
- LLM-based intent routing with rule-based fallback.
- Query rewrite for follow-up questions and incomplete requests.
- LLM-first NL2SQL generation with deterministic fallback.
- LangGraph workflow for intent parsing, retrieval, SQL generation, validation, repair, and execution.
- Hybrid metadata retrieval with Qdrant, Elasticsearch, and MySQL fallback.
- Multi-step Planner for complex financial analysis.
- Replan retry when a subtask returns empty rows.
- Skill/Tool extension mechanism for financial analytics.
- CSV ingestion with encoding detection, header cleanup, type inference, dynamic table creation, metadata registration, and index rebuild.
- Read-only SQL validation, table whitelist, LIMIT enforcement, and high-risk SQL blocking.
- Human-in-the-loop confirmation for risky queries.
- Persistent chat sessions and short-term memory.
- Trace logging for requests, nodes, model calls, tool calls, and errors.
- Automated evaluation for NL2SQL and Planner behavior.
- Background task support for asynchronous evaluation jobs.

### Quick Start

1. Start Docker Desktop.

2. Start infrastructure:

```powershell
docker compose -f infra\docker-compose.yml up -d
```

3. Activate the Python virtual environment:

```powershell
.\.venv\Scripts\Activate.ps1
```

Install backend dependencies on first setup:

```powershell
pip install -r backend\requirements.txt
```

4. Configure environment variables:

```powershell
Copy-Item .env.example .env
```

Edit `.env` with your own OpenAI-compatible LLM endpoint and API key.

5. Initialize database and indexes:

```powershell
$env:PYTHONPATH="$PWD\backend"
python backend\app\db\init_db.py
python -c "from app.services.metadata_indexer import MetadataIndexer; print(MetadataIndexer().rebuild())"
```

6. Start backend:

```powershell
$env:PYTHONPATH="$PWD\backend"
.\.venv\Scripts\uvicorn.exe app.main:app --app-dir backend --host 127.0.0.1 --port 8000
```

7. Start frontend:

```powershell
cd frontend
npm install
npm run dev
```

8. Open:

```text
http://127.0.0.1:5173
```

### Repository Update

Recommended commands:

```powershell
git status
git add README.md .gitignore .env.example backend frontend agent_extensions infra data_samples docs
git status
git commit -m "Enhance financial data agent system"
git push origin main
```

Do not commit `.env`, virtual environments, runtime logs, dependency folders, build outputs, snapshots, or temporary files.

### License

This project is intended for learning, portfolio demonstration, and engineering practice. Please review data source licenses and API provider terms before production use.
