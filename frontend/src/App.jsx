import { useState } from 'react';
import GraphVisualizer from './components/GraphVisualizer';
import ChatInterface from './components/ChatInterface';

function App() {
  const [highlightedNodes, setHighlightedNodes] = useState([]);

  return (
    <div className="app-container">
      <div className="graph-container">
        <div className="top-bar">
          <span style={{ fontWeight: 600, color: '#0f172a', fontSize: 13 }}>ERP Graph · Order-to-Cash</span>
          <span style={{ color: '#94a3b8', fontSize: 12 }}>|</span>
          <span>Scroll to zoom · Drag to pan · Hover nodes for detail</span>
          {highlightedNodes.length > 0 && (
            <span style={{
              marginLeft: 'auto',
              background: '#dbeafe',
              color: '#1d4ed8',
              padding: '2px 10px',
              borderRadius: 20,
              fontSize: 11,
              fontWeight: 600,
            }}>
              {highlightedNodes.length} nodes highlighted from query
            </span>
          )}
        </div>
        <GraphVisualizer highlightedNodes={highlightedNodes} />
      </div>
      <ChatInterface onHighlightNodes={setHighlightedNodes} />
    </div>
  );
}

export default App;
