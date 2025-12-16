import React, { useMemo } from 'react';
import { downloadSVGAsPNG } from '../utils/download';

const DelegationMap = ({ dreps, delegators, currentEpoch = 0, width = 800, height = 400 }) => {
  // Margins and drawing area
  const margin = { top: 60, right: 20, bottom: 40, left: 20 };
  const drawWidth = width - margin.left - margin.right;
  const drawHeight = height - margin.top - margin.bottom;

  // Y-positions
  const yDrep = margin.top;
  const yDelegator = height - margin.bottom;

  // Scales
  const xScale = (val) => margin.left + val * drawWidth;

  // Memoize calculations for performance
  const vizData = useMemo(() => {
    if (!dreps || !delegators) return { edges: [], drepNodes: [], delegatorNodes: [] };

    // 1. DRep Nodes
    const drepNodes = dreps.map(d => ({
      id: d.id,
      x: xScale(d.opinion),
      y: yDrep,
      // Use w_prime (total power) if available, else stake. 
      // Scale: smaller base multiplier, capped at 40px radius
      r: Math.min(40, Math.max(2, Math.sqrt(d.w_prime || d.stake) * 3)), 
      color: '#4F46E5', // Indigo 600
      isTarget: false
    }));

    // Map for quick lookup
    const drepMap = new Map(drepNodes.map(d => [d.id, d]));

    // 2. Delegator Nodes & Edges
    const delegatorNodes = [];
    const edges = [];

    delegators.forEach(d => {
      const x = xScale(d.opinion);
      const y = yDelegator;
      
      delegatorNodes.push({
        id: d.id,
        x,
        y,
        r: 2, // Fixed small size
        color: d.is_frozen ? '#F59E0B' : '#10B981' // Amber (Frozen) vs Emerald (Active)
      });

      if (d.current_drep_id) {
        const target = drepMap.get(d.current_drep_id);
        if (target) {
          edges.push({
            id: `${d.id}-${target.id}`,
            x1: x,
            y1: y,
            x2: target.x,
            y2: target.y,
            opacity: 0.3 // More visible lines
          });
        }
      }
    });

    return { edges, drepNodes, delegatorNodes };
  }, [dreps, delegators, width, height]);

  const handleDownload = () => {
    const svg = document.getElementById('delegation-map-svg');
    if (svg) {
        downloadSVGAsPNG(svg, 'delegation_map_snapshot.png', 3); // Higher scale for map details
    }
  };

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-4 overflow-hidden relative group">
      <div className="absolute top-4 right-4 z-10 opacity-0 group-hover:opacity-100 transition-opacity">
          <button 
            onClick={handleDownload}
            className="p-1.5 bg-white/90 hover:bg-white text-gray-600 hover:text-indigo-600 rounded-lg shadow-sm border border-gray-200"
            title="Download Map Snapshot"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" /></svg>
          </button>
      </div>
      <h3 className="text-sm font-bold text-gray-700 mb-2">Delegation Map</h3>
      <svg id="delegation-map-svg" width="100%" height="100%" viewBox={`0 0 ${width} ${height}`} className="w-full h-auto">
        {/* Background Grid */}
        <line x1={margin.left} y1={height/2} x2={width-margin.right} y2={height/2} stroke="#E5E7EB" strokeDasharray="4" />
        <line x1={margin.left} y1={height/2} x2={width-margin.right} y2={height/2} stroke="#E5E7EB" strokeDasharray="4" />
        <text x={width/2} y={height/2 - 5} textAnchor="middle" fontSize="10" fill="#9CA3AF">Opinion Spectrum [0, 1]</text>
        
        {/* Epoch Indicator - Top Right */}
        <text x={width - margin.right} y={25} textAnchor="end" fontSize="14" fontWeight="bold" fill="#374151">
            {currentEpoch === -1 ? "Initial State" : `Epoch: ${currentEpoch}`}
        </text>

        {/* Edges */}
        <g>
          {vizData.edges.map(e => (
            <line 
              key={e.id}
              x1={e.x1} y1={e.y1}
              x2={e.x2} y2={e.y2}
              stroke="#6B7280"
              strokeWidth="0.5"
              opacity={e.opacity}
              className="transition-all duration-500 ease-in-out"
            />
          ))}
        </g>

        {/* Delegators */}
        <g>
          {vizData.delegatorNodes.map(d => (
            <circle 
              key={d.id}
              cx={d.x} cy={d.y}
              r={d.r}
              fill={d.color}
              opacity="0.6"
              className="transition-all duration-500 ease-in-out"
            />
          ))}
          <text x={margin.left} y={yDelegator + 25} fontSize="10" fill="#6B7280" fontWeight="bold">Delegators</text>
        </g>

        {/* DReps */}
        <g>
          {vizData.drepNodes.map(d => (
            <rect 
              key={d.id}
              x={d.x - d.r} y={d.y - d.r}
              width={d.r * 2} height={d.r * 2}
              fill={d.color}
              stroke="white"
              strokeWidth="1"
              className="transition-all duration-500 ease-in-out"
            />
          ))}
          <text x={margin.left} y={yDrep - 15} fontSize="10" fill="#6B7280" fontWeight="bold">DReps</text>
        </g>
      </svg>
      <div className="flex justify-center space-x-4 mt-2 text-xs text-gray-500">
        <div className="flex items-center"><span className="w-2 h-2 rounded-full bg-emerald-500 mr-1"></span> Active Delegator</div>
        <div className="flex items-center"><span className="w-2 h-2 rounded-full bg-amber-500 mr-1"></span> Frozen Delegator</div>
        <div className="flex items-center"><span className="w-2 h-2 bg-indigo-600 mr-1"></span> DRep (Size = Stake)</div>
      </div>
    </div>
  );
};

export default DelegationMap;
