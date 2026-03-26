import { useState } from 'react';
import GraphVisualizer from './components/GraphVisualizer';
import ChatInterface from './components/ChatInterface';

function App() {
  const [highlightedNodes, setHighlightedNodes] = useState([]);
  
  return (
    <div className="app-container">
       <div className="graph-container">
          <GraphVisualizer highlightedNodes={highlightedNodes} />
       </div>
       <ChatInterface onHighlightNodes={setHighlightedNodes} />
    </div>
  );
}
export default App;
