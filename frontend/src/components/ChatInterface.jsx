import { useState, useRef, useEffect } from 'react';
import { Send, Zap, Database, ChevronDown, ChevronUp, BarChart3, AlertCircle, CheckCircle2, Clock } from 'lucide-react';

export default function ChatInterface({ onHighlightNodes }) {
  const [input, setInput] = useState('');
  const [messages, setMessages] = useState([
    { role: 'agent', text: "Hi! I can help you analyze the Order-to-Cash ERP process. Ask me anything about orders, deliveries, invoices, payments, or products." }
  ]);
  const [loading, setLoading] = useState(false);
  const [expandedSql, setExpandedSql] = useState({});
  const scrollRef = useRef();

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  const toggleSql = (idx) => {
    setExpandedSql(prev => ({ ...prev, [idx]: !prev[idx] }));
  };

  const sendQuery = async (userMsg) => {
    if (!userMsg.trim() || loading) return;

    setMessages(prev => [...prev, { role: 'user', text: userMsg }]);
    setInput('');
    setLoading(true);

    const startTime = Date.now();

    try {
      const apiUrl = import.meta.env.VITE_API_URL || '';
      const res = await fetch(`${apiUrl}/query`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: userMsg })
      });

      const data = await res.json();
      const elapsed = ((Date.now() - startTime) / 1000).toFixed(2);

      setMessages(prev => [...prev, {
        role: 'agent',
        text: data.answer || 'No response.',
        sql: data.sql,
        table: data.data,
        confidence: data.confidence,
        rows: data.rows_returned,
        elapsed,
        error: data.error,
        highlightCount: data.highlight_nodes?.length || 0,
      }]);

      if (data.highlight_nodes?.length) {
        onHighlightNodes(data.highlight_nodes);
      } else {
        onHighlightNodes([]);
      }

    } catch (err) {
      setMessages(prev => [...prev, {
        role: 'agent',
        text: 'Error communicating with the API. Make sure the backend is running.',
        error: err.message,
        confidence: 'error'
      }]);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    sendQuery(input);
  };

  const confidenceBadge = (confidence) => {
    if (!confidence) return null;
    const map = {
      high: { label: 'High Confidence', cls: 'badge-high', icon: <CheckCircle2 size={11} /> },
      low: { label: 'Low Confidence', cls: 'badge-low', icon: <AlertCircle size={11} /> },
      fallback: { label: 'Fallback Mode', cls: 'badge-fallback', icon: <AlertCircle size={11} /> },
      error: { label: 'Error', cls: 'badge-error', icon: <AlertCircle size={11} /> },
    };
    const b = map[confidence] || { label: confidence, cls: 'badge-low', icon: null };
    return <span className={`confidence-badge ${b.cls}`}>{b.icon}{b.label}</span>;
  };

  return (
    <div className="chat-panel">
      {/* Header */}
      <div className="chat-header">
        <div className="header-icon">
          <Zap size={15} fill="white" />
        </div>
        <div>
          <div className="title">Dodge AI Graph Agent</div>
          <div className="subtitle">Order-to-Cash Intelligence</div>
        </div>
        <div className="header-status">
          <span className="status-dot" />
          Live
        </div>
      </div>

      {/* Messages */}
      <div className="chat-messages" ref={scrollRef}>
        {messages.map((msg, idx) => (
          <div key={idx} className={`message ${msg.role}`}>
            {/* Bubble */}
            <div className="message-bubble">
              {msg.text}
            </div>

            {/* Metadata bar for agent responses */}
            {msg.role === 'agent' && (msg.confidence || msg.elapsed) && (
              <div className="msg-meta">
                {confidenceBadge(msg.confidence)}
                {msg.rows !== undefined && (
                  <span className="meta-chip">
                    <BarChart3 size={10} /> {msg.rows} rows
                  </span>
                )}
                {msg.elapsed && (
                  <span className="meta-chip">
                    <Clock size={10} /> {msg.elapsed}s
                  </span>
                )}
                {msg.highlightCount > 0 && (
                  <span className="meta-chip">
                    <Database size={10} /> {msg.highlightCount} nodes lit
                  </span>
                )}
              </div>
            )}

            {/* SQL toggle */}
            {msg.sql && (
              <div className="sql-section">
                <button className="sql-toggle" onClick={() => toggleSql(idx)}>
                  <Database size={11} />
                  SQL Executed
                  {expandedSql[idx] ? <ChevronUp size={11} /> : <ChevronDown size={11} />}
                </button>
                {expandedSql[idx] && (
                  <div className="sql-block">{msg.sql}</div>
                )}
              </div>
            )}

            {/* Results table */}
            {msg.table && msg.table.length > 0 && (
              <div className="table-wrapper">
                <div className="table-label">
                  <BarChart3 size={11} />
                  Results — {msg.table.length} record{msg.table.length !== 1 ? 's' : ''}
                </div>
                <div className="table-scroll">
                  <table className="results-table">
                    <thead>
                      <tr>
                        {Object.keys(msg.table[0]).map(k => (
                          <th key={k}>{k.replace(/_/g, ' ')}</th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {msg.table.slice(0, 8).map((row, i) => (
                        <tr key={i}>
                          {Object.values(row).map((v, j) => (
                            <td key={j} title={String(v)}>
                              {String(v) === 'null' ? <span className="null-val">—</span> : String(v)}
                            </td>
                          ))}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                  {msg.table.length > 8 && (
                    <div className="table-overflow-note">
                      Showing 8 of {msg.table.length} rows
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Error display */}
            {msg.error && (
              <div className="error-block">
                <AlertCircle size={12} />
                {msg.error}
              </div>
            )}
          </div>
        ))}

        {/* Loading indicator */}
        {loading && (
          <div className="message agent">
            <div className="message-bubble thinking">
              <span className="dot" /><span className="dot" /><span className="dot" />
            </div>
          </div>
        )}

        {/* Quick action suggestions — shown when idle */}
        {!loading && messages.length <= 2 && (
          <div className="quick-actions">
            <div className="quick-actions-label">Try asking:</div>
            <button className="quick-action-btn" onClick={() => sendQuery("Which products are associated with the highest number of billing documents?")}>
              📦 Top billed products
            </button>
            <button className="quick-action-btn" onClick={() => sendQuery("Identify sales orders that have been delivered but not billed")}>
              🚫 Orders without invoices
            </button>
            <button className="quick-action-btn" onClick={() => sendQuery("Show me the total payment amount per invoice")}>
              💰 Payments per invoice
            </button>
            <button className="quick-action-btn" onClick={() => sendQuery("List all customers and their order counts")}>
              👥 Customer order counts
            </button>
          </div>
        )}
      </div>

      {/* Input bar */}
      <form className="chat-input-container" onSubmit={handleSubmit}>
        <input
          autoFocus
          className="chat-input"
          placeholder={loading ? 'Analyzing...' : 'Ask about orders, deliveries, invoices...'}
          value={input}
          onChange={e => setInput(e.target.value)}
          disabled={loading}
        />
        <button type="submit" className="send-button" disabled={!input.trim() || loading}>
          <Send size={16} />
        </button>
      </form>
    </div>
  );
}
