import React, { useMemo, useState } from 'react';
import { createRoot } from 'react-dom/client';
import { Activity, Database, Loader2, Play, Search, Server, Sparkles, Upload } from 'lucide-react';
import './styles.css';

type ContextItem = {
  object_name: string;
  business_name: string;
  description: string;
  rank_score: number;
  sources: string[];
};

type QueryResult = {
  question: string;
  intent: string;
  sql: string;
  steps: string[];
  context: ContextItem[];
  columns: string[];
  rows: Record<string, unknown>[];
};

type UploadResult = {
  table_name: string;
  dataset_name: string;
  columns: { original_name: string; sql_name: string; mysql_type: string }[];
  rows_inserted: number;
  indexed: number;
};

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000';
const examples = ['净利润最高的股票', '银行行业ROE最高的公司', '市盈率最低的股票', '宁德时代动力电池装机量', '成交额最高的股票'];

function App() {
  const [question, setQuestion] = useState(examples[0]);
  const [limit, setLimit] = useState(5);
  const [result, setResult] = useState<QueryResult | null>(null);
  const [events, setEvents] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [uploadResult, setUploadResult] = useState<UploadResult | null>(null);
  const [error, setError] = useState('');

  const rowCount = result?.rows.length ?? 0;
  const contextCount = result?.context.length ?? 0;
  const hasResult = Boolean(result);

  async function runQuery(nextQuestion = question) {
    const trimmed = nextQuestion.trim();
    if (!trimmed) return;
    setQuestion(trimmed);
    setLoading(true);
    setError('');
    setEvents(['提交自然语言问题']);
    setResult(null);
    try {
      const response = await fetch(`${API_BASE}/api/nl2sql/stream`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question: trimmed, limit }),
      });
      if (!response.ok || !response.body) {
        throw new Error('流式查询启动失败');
      }
      const reader = response.body.getReader();
      const decoder = new TextDecoder('utf-8');
      let buffer = '';
      while (true) {
        const { value, done } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        const chunks = buffer.split('\n\n');
        buffer = chunks.pop() ?? '';
        for (const chunk of chunks) {
          handleSseChunk(chunk);
        }
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : '查询失败');
    } finally {
      setLoading(false);
    }
  }

  async function uploadCsv(event: React.ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    event.target.value = '';
    if (!file) return;
    setUploading(true);
    setError('');
    try {
      const form = new FormData();
      form.append('file', file);
      form.append('dataset_name', file.name.replace(/\.csv$/i, ''));
      const response = await fetch(`${API_BASE}/api/datasets/upload`, {
        method: 'POST',
        body: form,
      });
      if (!response.ok) {
        const payload = await response.json().catch(() => null);
        throw new Error(payload?.detail || 'CSV 导入失败');
      }
      const payload = await response.json() as UploadResult;
      setUploadResult(payload);
      setQuestion(`查询${payload.dataset_name}数据`);
      setEvents(['CSV 上传', '自动建表', '写入元数据', '重建索引']);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'CSV 导入失败');
    } finally {
      setUploading(false);
    }
  }

  function handleSseChunk(chunk: string) {
    const eventLine = chunk.split('\n').find((line) => line.startsWith('event:'));
    const dataLine = chunk.split('\n').find((line) => line.startsWith('data:'));
    if (!eventLine || !dataLine) return;
    const eventName = eventLine.replace('event:', '').trim();
    const payload = JSON.parse(dataLine.replace('data:', '').trim());
    if (eventName === 'step') {
      setEvents((current) => [...current, payload.name]);
    }
    if (eventName === 'result') {
      setResult(payload as QueryResult);
      setEvents((current) => payload.steps?.length ? payload.steps : current);
    }
    if (eventName === 'error') {
      setError(payload.message || '查询失败');
    }
  }

  const tableRows = useMemo(() => result?.rows ?? [], [result]);

  return (
    <main className="app-shell">
      <aside className="sidebar">
        <div className="brand-row">
          <div className="brand-mark"><Sparkles size={18} /></div>
          <div>
            <h1>NL2SQL</h1>
            <p>金融数据智能查询系统</p>
          </div>
        </div>

        <section className="status-panel">
          <div className="status-item"><Server size={16} /><span>FastAPI</span><strong>8000</strong></div>
          <div className="status-item"><Database size={16} /><span>MySQL / Qdrant / ES</span><strong>在线</strong></div>
          <div className="status-item"><Activity size={16} /><span>LangGraph Workflow</span><strong>{events.length || 0}</strong></div>
        </section>

        <section className="examples">
          <h2>示例问题</h2>
          {examples.map((item) => (
            <button key={item} type="button" onClick={() => runQuery(item)} disabled={loading}>
              {item}
            </button>
          ))}
        </section>

        <section className="upload-panel">
          <h2>CSV 数据导入</h2>
          <label className="upload-button">
            {uploading ? <Loader2 className="spin" size={16} /> : <Upload size={16} />}
            <span>{uploading ? '导入中' : '上传 CSV'}</span>
            <input type="file" accept=".csv,text/csv" onChange={uploadCsv} disabled={uploading} />
          </label>
          {uploadResult && (
            <div className="upload-result">
              <strong>{uploadResult.dataset_name}</strong>
              <span>{uploadResult.table_name}</span>
              <small>{uploadResult.rows_inserted} 行 · {uploadResult.columns.length} 列</small>
              <button type="button" onClick={() => runQuery(`查询${uploadResult.dataset_name}数据`)} disabled={loading}>
                查询这份数据
              </button>
            </div>
          )}
        </section>
      </aside>

      <section className="workspace">
        <div className="query-bar">
          <Search size={20} />
          <textarea value={question} onChange={(event) => setQuestion(event.target.value)} rows={2} />
          <label className="limit-control">
            <span>返回</span>
            <input type="number" min={1} max={50} value={limit} onChange={(event) => setLimit(Number(event.target.value))} />
          </label>
          <button className="run-button" type="button" onClick={() => runQuery()} disabled={loading}>
            {loading ? <Loader2 className="spin" size={18} /> : <Play size={18} />}
            查询
          </button>
        </div>

        {error && <div className="error-strip">{error}</div>}

        <div className="metric-grid">
          <Metric label="查询意图" value={result?.intent || '等待查询'} />
          <Metric label="检索上下文" value={`${contextCount} 条`} />
          <Metric label="结果行数" value={`${rowCount} 行`} />
        </div>

        <div className="content-grid">
          <section className="panel steps-panel">
            <h2>执行流程</h2>
            <div className="step-list">
              {(events.length ? events : ['parse_intent', 'retrieve_context', 'generate_sql', 'validate_sql', 'execute_sql']).map((step, index) => (
                <div className={`step ${hasResult || index < events.length ? 'done' : ''}`} key={`${step}-${index}`}>
                  <span>{index + 1}</span>
                  <strong>{step}</strong>
                </div>
              ))}
            </div>
          </section>

          <section className="panel sql-panel">
            <h2>生成 SQL</h2>
            <pre>{result?.sql || '查询后展示生成的 SELECT 语句'}</pre>
          </section>
        </div>

        <section className="panel context-panel">
          <h2>检索上下文</h2>
          <div className="context-list">
            {(result?.context ?? []).map((item) => (
              <article key={`${item.object_name}-${item.rank_score}`}>
                <div>
                  <strong>{item.business_name}</strong>
                  <span>{item.object_name}</span>
                </div>
                <p>{item.description}</p>
                <small>{item.sources.join(' + ')} · {item.rank_score.toFixed(3)}</small>
              </article>
            ))}
            {!result && <p className="empty-text">这里会展示 Qdrant、Elasticsearch 与 MySQL 合并后的元数据召回结果。</p>}
          </div>
        </section>

        <section className="panel result-panel">
          <h2>查询结果</h2>
          {result && tableRows.length > 0 ? (
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>{result.columns.map((column) => <th key={column}>{column}</th>)}</tr>
                </thead>
                <tbody>
                  {tableRows.map((row, rowIndex) => (
                    <tr key={rowIndex}>
                      {result.columns.map((column) => <td key={column}>{String(row[column] ?? '')}</td>)}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <p className="empty-text">暂无结果。</p>
          )}
        </section>
      </section>
    </main>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="metric">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);

