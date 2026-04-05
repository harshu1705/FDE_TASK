import { useEffect, useState, useRef, useMemo, useCallback } from 'react';
import ForceGraph2D from 'react-force-graph-2d';

const NODE_COLORS = {
  order:      { color: '#3b82f6', label: 'Order' },
  customer:   { color: '#0ea5e9', label: 'Customer' },
  delivery:   { color: '#22c55e', label: 'Delivery' },
  invoice:    { color: '#f97316', label: 'Invoice' },
  payment:    { color: '#ef4444', label: 'Payment' },
  product:    { color: '#a855f7', label: 'Product' },
  order_item: { color: '#f59e0b', label: 'Item' },
};

export default function GraphVisualizer({ highlightedNodes }) {
  const [graphData, setGraphData] = useState({ nodes: [], links: [] });
  const [loading, setLoading] = useState(true);
  const [error, setError]     = useState(null);
  const [stats, setStats]     = useState({ nodes: 0, links: 0 });
  const graphRef = useRef();

  useEffect(() => {
    const apiUrl = import.meta.env.VITE_API_URL || '';
    setLoading(true);
    setError(null);
    fetch(`${apiUrl}/api/graph/all`)
      .then(res => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return res.json();
      })
      .then(data => {
        setGraphData(data);
        setStats({ nodes: data.nodes?.length || 0, links: data.links?.length || 0 });
        setLoading(false);
      })
      .catch(err => {
        console.error('Could not fetch graph:', err);
        setError('Could not load graph. Is the backend running?');
        setLoading(false);
      });
  }, []);

  const highlightSet = useMemo(() => new Set(highlightedNodes), [highlightedNodes]);

  const getNodeColor = (node) => {
    const def = NODE_COLORS[node.group];
    return def ? def.color : '#cbd5e1';
  };

  const paintNode = useCallback((node, ctx, globalScale) => {
    const isHighlighted = highlightSet.size === 0 || highlightSet.has(node.id);
    const label   = node.label || node.id;
    const fontSize = Math.max(4, 11 / globalScale);
    const baseSize = highlightSet.size > 0 ? (isHighlighted ? 7 : 3) : 5;
    const color   = getNodeColor(node);

    // Draw node circle
    ctx.beginPath();
    ctx.arc(node.x, node.y, baseSize, 0, 2 * Math.PI, false);
    ctx.fillStyle = isHighlighted ? color : 'rgba(203,213,225,0.5)';
    ctx.fill();

    // Glow + border for highlighted nodes
    if (isHighlighted && highlightSet.size > 0) {
      ctx.shadowColor  = color;
      ctx.shadowBlur   = 14;
      ctx.lineWidth    = 1.5;
      ctx.strokeStyle  = '#ffffff';
      ctx.stroke();
      ctx.shadowBlur   = 0;
    }

    // Draw label when zoomed in enough
    if (isHighlighted && globalScale > 1.5) {
      ctx.font          = `${fontSize}px Inter, sans-serif`;
      ctx.textAlign     = 'center';
      ctx.textBaseline  = 'top';
      ctx.fillStyle     = '#0f172a';
      ctx.fillText(label, node.x, node.y + baseSize + 2);
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [highlightSet]);

  const linkColor = useCallback((link) => {
    const s = typeof link.source === 'object' ? link.source.id : link.source;
    const t = typeof link.target === 'object' ? link.target.id : link.target;
    return (highlightSet.has(s) || highlightSet.has(t)) ? '#3b82f6' : '#e2e8f0';
  }, [highlightSet]);

  const linkWidth = useCallback((link) => {
    const s = typeof link.source === 'object' ? link.source.id : link.source;
    const t = typeof link.target === 'object' ? link.target.id : link.target;
    return (highlightSet.has(s) || highlightSet.has(t)) ? 2 : 0.8;
  }, [highlightSet]);

  return (
    <div style={{ width: '100%', height: '100%', position: 'relative', background: '#f8fafc' }}>

      {/* Loading overlay */}
      {loading && (
        <div style={overlayStyle}>
          <div style={spinnerStyle} />
          <span style={{ fontSize: 13, color: '#475569', marginTop: 12 }}>Loading ERP graph…</span>
        </div>
      )}

      {/* Error overlay */}
      {error && !loading && (
        <div style={{ ...overlayStyle, flexDirection: 'column', gap: 8 }}>
          <span style={{ fontSize: 28 }}>⚠️</span>
          <span style={{ fontSize: 13, color: '#dc2626', maxWidth: 280, textAlign: 'center' }}>{error}</span>
          <span style={{ fontSize: 11, color: '#94a3b8' }}>Graph will show fallback data</span>
        </div>
      )}

      {/* Graph */}
      {!loading && (
        <ForceGraph2D
          ref={graphRef}
          graphData={graphData}
          nodeCanvasObject={paintNode}
          nodeCanvasObjectMode={() => 'replace'}
          linkColor={linkColor}
          linkWidth={linkWidth}
          linkDirectionalArrowLength={4}
          linkDirectionalArrowRelPos={1}
          linkDirectionalParticles={(link) => {
            const s = typeof link.source === 'object' ? link.source.id : link.source;
            const t = typeof link.target === 'object' ? link.target.id : link.target;
            return (highlightSet.has(s) || highlightSet.has(t)) ? 2 : 0;
          }}
          linkDirectionalParticleSpeed={0.006}
          linkDirectionalParticleColor={() => '#3b82f6'}
          backgroundColor="#f8fafc"
          d3AlphaDecay={0.04}
          d3VelocityDecay={0.25}
          cooldownTicks={200}
          onEngineStop={() => {
            if (graphRef.current) {
              graphRef.current.zoomToFit(400, 50);
            }
          }}
        />
      )}

      {/* Legend */}
      {!loading && (
        <div style={legendStyle}>
          {Object.entries(NODE_COLORS).map(([key, { color, label }]) => (
            <div key={key} style={legendItemStyle}>
              <span style={{ ...legendDotStyle, background: color }} />
              <span>{label}</span>
            </div>
          ))}
        </div>
      )}

      {/* Stats pill */}
      {!loading && stats.nodes > 0 && (
        <div style={statsPillStyle}>
          {stats.nodes} nodes · {stats.links} edges
          {highlightSet.size > 0 && <span style={{ color: '#3b82f6' }}> · {highlightSet.size} highlighted</span>}
        </div>
      )}
    </div>
  );
}

/* ─── Inline styles for pure-JSX overlays ─────────────────────── */
const overlayStyle = {
  position: 'absolute', inset: 0,
  display: 'flex', flexDirection: 'column',
  alignItems: 'center', justifyContent: 'center',
  background: 'rgba(248,250,252,0.85)',
  zIndex: 20, backdropFilter: 'blur(4px)',
};

const spinnerStyle = {
  width: 36, height: 36,
  border: '3px solid #e2e8f0',
  borderTop: '3px solid #3b82f6',
  borderRadius: '50%',
  animation: 'spin 0.8s linear infinite',
};

// inject keyframes once
if (typeof document !== 'undefined' && !document.getElementById('gv-spin')) {
  const s = document.createElement('style');
  s.id = 'gv-spin';
  s.textContent = '@keyframes spin { to { transform: rotate(360deg); } }';
  document.head.appendChild(s);
}

const legendStyle = {
  position: 'absolute', bottom: 20, left: 20,
  display: 'flex', flexDirection: 'column', gap: 5,
  background: 'rgba(255,255,255,0.92)',
  backdropFilter: 'blur(6px)',
  padding: '10px 14px',
  borderRadius: 10,
  border: '1px solid #e2e8f0',
  boxShadow: '0 2px 12px rgba(15,23,42,0.08)',
  zIndex: 10,
};

const legendItemStyle = {
  display: 'flex', alignItems: 'center', gap: 7,
  fontSize: 11, color: '#475569', fontFamily: 'Inter, sans-serif',
};

const legendDotStyle = {
  width: 9, height: 9, borderRadius: '50%', flexShrink: 0,
};

const statsPillStyle = {
  position: 'absolute', top: 52, left: '50%', transform: 'translateX(-50%)',
  background: 'rgba(255,255,255,0.92)',
  backdropFilter: 'blur(6px)',
  padding: '4px 14px',
  borderRadius: 20,
  border: '1px solid #e2e8f0',
  fontSize: 11, color: '#64748b',
  fontFamily: 'Inter, sans-serif',
  fontVariantNumeric: 'tabular-nums',
  zIndex: 10,
  boxShadow: '0 1px 6px rgba(15,23,42,0.06)',
  whiteSpace: 'nowrap',
};
