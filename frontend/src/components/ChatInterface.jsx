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

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!input.trim() || loading) return;

    const userMsg = input.trim();
    setMessages(prev => [...prev, { role: 'user', text: userMsg }]);
    setInput('');
    setLoading(true);

    try {
      const res = await fetch("http://localhost:8000/query", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: userMsg })
      });
      
      const data = await res.json();
      
      setMessages(prev => [...prev, { role: 'agent', text: data.answer || "No response." }]);
      
      if (data.highlight_nodes) {
        onHighlightNodes(data.highlight_nodes);
      } else {
        onHighlightNodes([]);
      }
      
    } catch (err) {
      setMessages(prev => [...prev, { role: 'agent', text: "Error communicating with the backend API." }]);
    } finally {
      setLoading(false);
    }
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
           </div>
         ))}
         {loading && (
           <div className="message agent">
             <div className="message-bubble" style={{ opacity: 0.6 }}>Thinking...</div>
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
