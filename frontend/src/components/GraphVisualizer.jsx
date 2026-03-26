import { useEffect, useState, useRef, useMemo, useCallback } from 'react';
import ForceGraph2D from 'react-force-graph-2d';

export default function GraphVisualizer({ highlightedNodes }) {
  const [graphData, setGraphData] = useState({ nodes: [], links: [] });
  const graphRef = useRef();

  useEffect(() => {
    const apiUrl = import.meta.env.VITE_API_URL || "http://localhost:8000";
    fetch(`${apiUrl}/api/graph/all`)
      .then(res => res.json())
      .then(data => setGraphData(data))
      .catch(err => console.error("Could not fetch graph:", err));
  }, []);

  const highlightSet = useMemo(() => new Set(highlightedNodes), [highlightedNodes]);

  const paintNode = useCallback((node, ctx, globalScale) => {
    const isHighlighted = highlightSet.size === 0 || highlightSet.has(node.id);
    const label = node.label || node.id;
    const fontSize = 12 / globalScale;

    const size = isHighlighted ? (highlightSet.size > 0 ? 8 : 5) : 3;
    ctx.beginPath();
    ctx.arc(node.x, node.y, size, 0, 2 * Math.PI, false);

    // Color based on type: order -> blue, delivery -> green, invoice -> orange, payment -> red
    let color = "#cbd5e1"; // default grey
    if (node.group === "order") color = "#3b82f6"; // blue
    if (node.group === "delivery") color = "#22c55e"; // green
    if (node.group === "invoice") color = "#f97316"; // orange
    if (node.group === "payment") color = "#ef4444"; // red
    if (node.group === "product") color = "#a855f7"; // purple
    if (node.group === "customer") color = "#0ea5e9"; // cyan

    ctx.fillStyle = isHighlighted ? color : "#f1f5f9";
    ctx.fill();

    if (isHighlighted && highlightSet.size > 0) {
      ctx.shadowColor = color;
      ctx.shadowBlur = 10;
      ctx.lineWidth = 2;
      ctx.strokeStyle = "#fff";
      ctx.stroke();
      ctx.shadowBlur = 0;
    } else if (!isHighlighted) {
      ctx.strokeStyle = "#cbd5e1";
      ctx.lineWidth = 0.5;
      ctx.stroke();
    }

    if (isHighlighted && globalScale > 1) {
      ctx.font = `${fontSize}px Inter, sans-serif`;
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      ctx.fillStyle = isHighlighted ? "#0f172a" : "#94a3b8";
      ctx.fillText(label, node.x, node.y + size + fontSize + 2);
    }
  }, [highlightSet]);

  return (
    <div style={{ width: '100%', height: '100%', background: '#ffffff' }}>
      <ForceGraph2D
        ref={graphRef}
        graphData={graphData}
        nodeCanvasObject={paintNode}
        linkColor={(link) => {
          const s = typeof link.source === 'object' ? link.source.id : link.source;
          const t = typeof link.target === 'object' ? link.target.id : link.target;
          return highlightSet.has(s) || highlightSet.has(t) 
            ? "#3b82f6" : "#e2e8f0";
        }}
        linkWidth={(link) => {
          const s = typeof link.source === 'object' ? link.source.id : link.source;
          const t = typeof link.target === 'object' ? link.target.id : link.target;
          return highlightSet.has(s) || highlightSet.has(t) ? 2 : 1;
        }}
        backgroundColor="#ffffff"
        d3AlphaDecay={0.05}
        d3VelocityDecay={0.2}
        cooldownTicks={150}
        onEngineStop={() => {
           if (graphRef.current) {
             graphRef.current.zoomToFit(200, 30);
           }
        }}
      />
    </div>
  );
}
