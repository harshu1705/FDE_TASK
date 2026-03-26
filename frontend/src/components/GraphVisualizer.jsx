import { useEffect, useState, useRef, useMemo, useCallback } from 'react';
import ForceGraph2D from 'react-force-graph-2d';

export default function GraphVisualizer({ highlightedNodes }) {
  const [graphData, setGraphData] = useState({ nodes: [], links: [] });
  const graphRef = useRef();

  useEffect(() => {
    fetch('http://localhost:8000/api/graph/all')
      .then(res => res.json())
      .then(data => setGraphData(data))
      .catch(err => console.error("Could not fetch graph:", err));
  }, []);

  const highlightSet = useMemo(() => new Set(highlightedNodes), [highlightedNodes]);

  const paintNode = useCallback((node, ctx, globalScale) => {
    const isHighlighted = highlightSet.size === 0 || highlightSet.has(node.id);
    const label = node.label || node.id;
    const fontSize = 12 / globalScale;

    // Node Size
    const size = isHighlighted ? (highlightSet.size > 0 ? 8 : 4) : 2;
    ctx.beginPath();
    ctx.arc(node.x, node.y, size, 0, 2 * Math.PI, false);

    // Color based on group
    let color = "#cbd5e1";
    if (node.group === "order") color = "#fcd34d";
    if (node.group === "delivery") color = "#60a5fa";
    if (node.group === "invoice") color = "#34d399";
    if (node.group === "payment") color = "#a78bfa";
    if (node.group === "product") color = "#f472b6";
    if (node.group === "customer") color = "#fb923c";

    ctx.fillStyle = isHighlighted ? color : "#1e293b";
    ctx.fill();

    // Subtle glow if directly targeted by highlight
    if (isHighlighted && highlightSet.size > 0) {
      ctx.shadowColor = color;
      ctx.shadowBlur = 12;
      ctx.lineWidth = 2;
      ctx.strokeStyle = "#fff";
      ctx.stroke();
      ctx.shadowBlur = 0; // reset
    } else if (!isHighlighted) {
      ctx.strokeStyle = "rgba(0,0,0,0.5)";
      ctx.lineWidth = 0.5;
      ctx.stroke();
    }

    // Label on hover or highlight if zoomed in
    if (isHighlighted && globalScale > 0.8) {
      ctx.font = `${fontSize}px Inter, sans-serif`;
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      ctx.fillStyle = isHighlighted ? "rgba(255,255,255,0.9)" : "rgba(255,255,255,0.3)";
      ctx.fillText(label, node.x, node.y + size + fontSize + 2);
    }
  }, [highlightSet]);

  return (
    <div style={{ width: '100%', height: '100%', background: '#0d1117' }}>
      <ForceGraph2D
        ref={graphRef}
        graphData={graphData}
        nodeCanvasObject={paintNode}
        nodePointerAreaPaint={(node, color, ctx) => {
          ctx.fillStyle = color;
          ctx.beginPath();
          ctx.arc(node.x, node.y, 10, 0, 2 * Math.PI, false);
          ctx.fill();
        }}
        linkColor={(link) => {
          const s = typeof link.source === 'object' ? link.source.id : link.source;
          const t = typeof link.target === 'object' ? link.target.id : link.target;
          return highlightSet.has(s) || highlightSet.has(t) 
            ? "rgba(100,200,255,0.6)" : "rgba(100,100,100,0.15)";
        }}
        linkWidth={(link) => {
          const s = typeof link.source === 'object' ? link.source.id : link.source;
          const t = typeof link.target === 'object' ? link.target.id : link.target;
          return highlightSet.has(s) || highlightSet.has(t) ? 2 : 0.5;
        }}
        backgroundColor="#0d1117"
        d3AlphaDecay={0.05}
        d3VelocityDecay={0.2}
        cooldownTicks={150}
        onEngineStop={() => {
           if (graphRef.current) {
             graphRef.current.zoomToFit(200, 20);
           }
        }}
      />
    </div>
  );
}
