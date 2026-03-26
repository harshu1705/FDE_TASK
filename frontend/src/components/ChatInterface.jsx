import { useState, useRef, useEffect } from 'react';
import { Send } from 'lucide-react';

export default function ChatInterface({ onHighlightNodes }) {
  const [input, setInput] = useState('');
  const [messages, setMessages] = useState([
    { role: 'agent', text: "Hi! I can help you analyze the Order to Cash process. Ask me anything." }
  ]);
  const [loading, setLoading] = useState(false);
  const scrollRef = useRef();

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  const sendQuery = async (userMsg) => {
    if (!userMsg.trim() || loading) return;

    setMessages(prev => [...prev, { role: 'user', text: userMsg }]);
    setInput('');
    setLoading(true);

    try {
      const apiUrl = import.meta.env.VITE_API_URL || "http://localhost:8000";
      const res = await fetch(`${apiUrl}/query`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: userMsg })
      });
      
      const data = await res.json();
      
      setMessages(prev => [...prev, { 
        role: 'agent', 
        text: data.answer || "No response.", 
        sql: data.sql, 
        table: data.data 
      }]);
      
      if (data.highlight_nodes) {
        onHighlightNodes(data.highlight_nodes);
      } else {
        onHighlightNodes([]);
      }
      
    } catch (err) {
      setMessages(prev => [...prev, { role: 'agent', text: "Error communicating with the API." }]);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    sendQuery(input);
  };

  return (
    <div className="chat-panel">
      <div className="chat-header">
         <div className="header-icon">D</div>
         <div>
           <div className="title">Dodge AI Graph Agent</div>
           <div className="subtitle">Order to Cash Analysis</div>
         </div>
      </div>
      
      <div className="chat-messages" ref={scrollRef}>
         {messages.map((msg, idx) => (
           <div key={idx} className={`message ${msg.role}`}>
             <div className="message-bubble">{msg.text}</div>
             {msg.sql && (
               <div className="sql-block">
                 <strong>SQL EXECUTED:</strong><br/>
                 {msg.sql}
               </div>
             )}
             {msg.table && msg.table.length > 0 && (
               <div className="table-block">
                 <table>
                   <thead>
                     <tr>
                       {Object.keys(msg.table[0]).map(k => <th key={k}>{k}</th>)}
                     </tr>
                   </thead>
                   <tbody>
                     {msg.table.slice(0, 5).map((row, i) => (
                       <tr key={i}>
                         {Object.values(row).map((v, j) => <td key={j}>{String(v)}</td>)}
                       </tr>
                     ))}
                   </tbody>
                 </table>
                 {msg.table.length > 5 && <div style={{fontSize: '10px', padding: '4px 8px', color: '#64748b'}}>Showing 5 of {msg.table.length} rows...</div>}
               </div>
             )}
           </div>
         ))}
         {loading && (
           <div className="message agent">
             <div className="message-bubble" style={{ opacity: 0.6 }}>Thinking...</div>
           </div>
         )}
         
         {/* Demo Buttons */}
         {!loading && (
           <div className="quick-actions">
             <button className="quick-action-btn" onClick={() => sendQuery("Which products are associated with the highest number of billing documents?")}>
               Top products
             </button>
             <button className="quick-action-btn" onClick={() => sendQuery("Identify sales orders that have broken flows (delivered but not billed)")}>
               Orders without invoices
             </button>
             <button className="quick-action-btn" onClick={() => sendQuery("Trace the full flow for a given billing document")}>
               Trace order
             </button>
           </div>
         )}
      </div>

      <form className="chat-input-container" onSubmit={handleSubmit}>
        <input 
          autoFocus
          className="chat-input"
          placeholder={loading ? "Waiting..." : "Ask a question..."}
          value={input}
          onChange={e => setInput(e.target.value)}
          disabled={loading}
        />
        <button type="submit" className="send-button" disabled={!input.trim() || loading}>
          <Send size={18} />
        </button>
      </form>
    </div>
  );
}
