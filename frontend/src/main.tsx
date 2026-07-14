import React, { useMemo, useState } from 'react';
import { createRoot } from 'react-dom/client';
import { Bot, Brain, Database, Loader2, MessageSquare, Send, Trash2, Upload, UserRound } from 'lucide-react';
import './styles.css';

type ContextItem = {
  object_name: string;
  business_name: string;
  description: string;
  rank_score: number;
  sources: string[];
};

type ChatResponse = {
  trace_id?: string;
  session_id: string;
  route: string;
  answer: string;
  question: string;
  intent?: string;
  sql?: string;
  steps: string[];
  context: ContextItem[];
  columns: string[];
  rows: Record<string, unknown>[];
  matched_skills: {
    name: string;
    display_name: string;
    description: string;
    prompt_hint: string;
    tools: string[];
  }[];
  tool_results: {
    name: string;
    display_name: string;
    description: string;
    output: Record<string, unknown>;
  }[];
  history: { role: string; content: string; created_at: string }[];
  requires_confirmation?: boolean;
  confirmation_reason?: string | null;
};

type ChatMessage = {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  route?: string;
};

type UploadResult = {
  table_name: string;
  dataset_name: string;
  columns: { original_name: string; sql_name: string; mysql_type: string }[];
  rows_inserted: number;
  indexed: number;
};

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000';
const SESSION_KEY = 'nl2sql_chat_session_id';
const examples = ['贵州茅台最近行情如何？', '分析银行行业ROE最高的公司', '市盈率最低的股票有哪些？', '对刚才的查询结果做一个总结', '查询我上传的CSV数据'];

function App() {
  const [sessionId, setSessionId] = useState(() => localStorage.getItem(SESSION_KEY) || '');
  const [input, setInput] = useState(examples[0]);
  const [limit, setLimit] = useState(8);
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: 'welcome',
      role: 'assistant',
      content: '你好，我可以查询股票行情、财务指标、因子指标，也可以分析查询结果。上传 CSV 后，我也能把新数据纳入自然语言查询。',
      route: 'general_chat',
    },
  ]);
  const [events, setEvents] = useState<string[]>([]);
  const [latest, setLatest] = useState<ChatResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [uploadResult, setUploadResult] = useState<UploadResult | null>(null);
  const [error, setError] = useState('');

  const tableRows = useMemo(() => latest?.rows ?? [], [latest]);

  async function sendMessage(nextInput = input, confirmed = false) {
    const message = nextInput.trim();
    if (!message || loading) return;
    setInput('');
    setError('');
    setEvents(['submit_message']);
    setLoading(true);
    setMessages((current) => [...current, { id: crypto.randomUUID(), role: 'user', content: message }]);
    try {
      const response = await fetch(`${API_BASE}/api/chat/stream`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message, session_id: sessionId || null, limit, confirmed }),
      });
      if (!response.ok || !response.body) {
        throw new Error('聊天请求启动失败');
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
      const messageText = err instanceof Error ? err.message : '聊天失败';
      setError(messageText);
      setMessages((current) => [...current, { id: crypto.randomUUID(), role: 'assistant', content: messageText, route: 'error' }]);
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
      const response = await fetch(`${API_BASE}/api/datasets/upload`, { method: 'POST', body: form });
      if (!response.ok) {
        const payload = await response.json().catch(() => null);
        throw new Error(payload?.detail || 'CSV 导入失败');
      }
      const payload = await response.json() as UploadResult;
      setUploadResult(payload);
      setMessages((current) => [
        ...current,
        {
          id: crypto.randomUUID(),
          role: 'assistant',
          content: `CSV 已导入：${payload.dataset_name}，写入 ${payload.rows_inserted} 行、${payload.columns.length} 列，并已重建检索索引。`,
          route: 'dataset_upload',
        },
      ]);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'CSV 导入失败');
    } finally {
      setUploading(false);
    }
  }

  async function clearMemory() {
    if (sessionId) {
      await fetch(`${API_BASE}/api/chat/sessions/${sessionId}`, { method: 'DELETE' }).catch(() => null);
    }
    localStorage.removeItem(SESSION_KEY);
    setSessionId('');
    setLatest(null);
    setEvents([]);
    setMessages([
      {
        id: 'welcome-reset',
        role: 'assistant',
        content: '短期记忆已清空。你可以重新开始提问。',
        route: 'general_chat',
      },
    ]);
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
      const result = payload as ChatResponse;
      setLatest(result);
      setSessionId(result.session_id);
      localStorage.setItem(SESSION_KEY, result.session_id);
      setMessages((current) => [
        ...current,
        { id: crypto.randomUUID(), role: 'assistant', content: result.answer, route: result.route },
      ]);
      setEvents(result.steps?.length ? ['route_intent', ...result.steps, 'answer'] : ['route_intent', 'answer']);
    }
    if (eventName === 'error') {
      setError(payload.message || '聊天失败');
    }
  }

  return (
    <main className="app-shell">
      <aside className="sidebar">
        <div className="brand-row">
          <div className="brand-mark"><Bot size={19} /></div>
          <div>
            <h1>NL2SQL Agent</h1>
            <p>金融数据聊天分析系统</p>
          </div>
        </div>

        <section className="status-panel">
          <div className="status-item"><Brain size={16} /><span>短期记忆</span><strong>{sessionId ? '已开启' : '新会话'}</strong></div>
          <div className="status-item"><Database size={16} /><span>SQL / RAG</span><strong>{latest?.route || '待路由'}</strong></div>
          <button className="clear-button" type="button" onClick={clearMemory}><Trash2 size={16} />清空记忆</button>
        </section>

        <section className="examples">
          <h2>示例问题</h2>
          {examples.map((item) => (
            <button key={item} type="button" onClick={() => sendMessage(item)} disabled={loading}>
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
            </div>
          )}
        </section>
      </aside>

      <section className="chat-workspace">
        <section className="chat-panel">
          <header className="chat-header">
            <div>
              <h2>多轮数据对话</h2>
              <span>{events.length ? events.join(' / ') : '等待输入'}</span>
            </div>
            <label className="limit-control">
              <span>返回行数</span>
              <input type="number" min={1} max={50} value={limit} onChange={(event) => setLimit(Number(event.target.value))} />
            </label>
          </header>

          {error && <div className="error-strip">{error}</div>}

          <div className="message-list">
            {messages.map((message) => (
              <article className={`message ${message.role}`} key={message.id}>
                <div className="avatar">{message.role === 'user' ? <UserRound size={17} /> : <Bot size={17} />}</div>
                <div className="bubble">
                  {message.route && <span className="route-label">{message.route}</span>}
                  <p>{message.content}</p>
                </div>
              </article>
            ))}
            {loading && (
              <article className="message assistant">
                <div className="avatar"><Bot size={17} /></div>
                <div className="bubble loading-bubble"><Loader2 className="spin" size={16} />思考中</div>
              </article>
            )}
            {latest?.requires_confirmation && (
              <article className="message assistant">
                <div className="avatar"><Bot size={17} /></div>
                <div className="bubble confirm-bubble">
                  <span className="route-label">human_in_the_loop</span>
                  <p>{latest.confirmation_reason || '该操作需要确认后执行。'}</p>
                  <button type="button" onClick={() => sendMessage(latest.question, true)} disabled={loading}>
                    确认执行
                  </button>
                </div>
              </article>
            )}
          </div>

          <form className="composer" onSubmit={(event) => { event.preventDefault(); sendMessage(); }}>
            <MessageSquare size={20} />
            <textarea value={input} onChange={(event) => setInput(event.target.value)} rows={2} />
            <button type="submit" disabled={loading || !input.trim()}>
              {loading ? <Loader2 className="spin" size={18} /> : <Send size={18} />}
            </button>
          </form>
        </section>

        <aside className="inspector">
          <section className="panel">
            <h2>执行详情</h2>
            <div className="detail-grid">
              <span>路由</span><strong>{latest?.route || '-'}</strong>
              <span>意图</span><strong>{latest?.intent || '-'}</strong>
              <span>记忆</span><strong>{latest?.history?.length ?? messages.length} 条</strong>
              <span>工具</span><strong>{latest?.tool_results?.length ?? 0} 个</strong>
            </div>
          </section>

          <section className="panel skill-panel">
            <h2>Skill / Tool</h2>
            <div className="skill-list">
              {(latest?.matched_skills ?? []).map((skill) => (
                <article key={skill.name}>
                  <strong>{skill.display_name}</strong>
                  <p>{skill.description}</p>
                  <small>{skill.tools.join(' / ')}</small>
                </article>
              ))}
              {(latest?.tool_results ?? []).map((tool) => (
                <article key={tool.name} className="tool-card">
                  <strong>{tool.display_name}</strong>
                  <p>{String(tool.output?.summary ?? tool.description)}</p>
                </article>
              ))}
              {!latest?.matched_skills?.length && !latest?.tool_results?.length && <p className="empty-text">暂无匹配 skill/tool。</p>}
            </div>
          </section>

          <section className="panel sql-panel">
            <h2>生成 SQL</h2>
            <pre>{latest?.sql || '无需 SQL 或尚未生成'}</pre>
          </section>

          <section className="panel context-panel">
            <h2>召回上下文</h2>
            <div className="context-list">
              {(latest?.context ?? []).map((item) => (
                <article key={`${item.object_name}-${item.rank_score}`}>
                  <strong>{item.business_name}</strong>
                  <span>{item.object_name}</span>
                  <p>{item.description}</p>
                </article>
              ))}
              {!latest?.context?.length && <p className="empty-text">暂无召回上下文。</p>}
            </div>
          </section>

          <section className="panel result-panel">
            <h2>查询结果</h2>
            {latest && tableRows.length > 0 ? (
              <div className="table-wrap">
                <table>
                  <thead>
                    <tr>{latest.columns.map((column) => <th key={column}>{column}</th>)}</tr>
                  </thead>
                  <tbody>
                    {tableRows.map((row, rowIndex) => (
                      <tr key={rowIndex}>
                        {latest.columns.map((column) => <td key={column}>{String(row[column] ?? '')}</td>)}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <p className="empty-text">暂无结果。</p>
            )}
          </section>
        </aside>
      </section>
    </main>
  );
}

createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
