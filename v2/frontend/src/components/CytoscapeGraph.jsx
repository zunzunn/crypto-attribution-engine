import React, { useEffect, useRef } from 'react';
import cytoscape from 'cytoscape';
import dagre from 'cytoscape-dagre';
import { ZoomIn, ZoomOut, Maximize2, RefreshCw } from 'lucide-react';
import { shortenAddress } from '../utils/formatters';

// Register dagre layout extension safely once
try {
  cytoscape.use(dagre);
} catch (e) {
  // already registered
}

export default function CytoscapeGraph({ traceData, selectedNode, onSelectNode }) {
  const containerRef = useRef(null);
  const cyRef = useRef(null);

  useEffect(() => {
    if (!containerRef.current || !traceData || !traceData.graph) return;

    // Convert graph + trace_results into cytoscape elements
    const elements = [];
    const nodeMap = new Map();

    const discoveredList = traceData.trace_results?.discovered_addresses || [];
    discoveredList.forEach(nodeInfo => {
      nodeMap.set(nodeInfo.address.toLowerCase(), nodeInfo);
    });

    // Helper to extract or fallback node info
    const getNodeInfo = (addr) => {
      const lower = addr.toLowerCase();
      if (nodeMap.has(lower)) return nodeMap.get(lower);
      return {
        address: addr,
        entity: "Unknown",
        entity_type: "Unknown",
        hop_distance: 0,
        risk: { score: 0, risk_level: "Low" }
      };
    };

    // Add nodes
    const addedNodeIds = new Set();
    const addNodeElement = (addr) => {
      const lower = addr.toLowerCase();
      if (addedNodeIds.has(lower)) return;
      addedNodeIds.add(lower);

      const info = getNodeInfo(addr);
      const isTarget = lower === (traceData.target_address || '').toLowerCase();
      const entityType = info.entity_type || 'Unknown';

      elements.push({
        data: {
          id: lower,
          label: info.entity !== 'Unknown' ? info.entity : shortenAddress(addr),
          fullAddress: addr,
          entity: info.entity,
          entityType: entityType,
          hopDistance: info.hop_distance ?? 0,
          riskScore: info.risk?.score ?? 0,
          riskLevel: info.risk?.risk_level ?? 'Low',
          isTarget: isTarget,
          info: info
        }
      });
    };

    // Add edges
    Object.entries(traceData.graph).forEach(([sourceAddr, txList]) => {
      addNodeElement(sourceAddr);
      txList.forEach((tx, idx) => {
        const targetAddr = tx.to;
        if (!targetAddr) return;
        addNodeElement(targetAddr);

        elements.push({
          data: {
            id: `edge_${sourceAddr}_${targetAddr}_${idx}`,
            source: sourceAddr.toLowerCase(),
            target: targetAddr.toLowerCase(),
            label: `${tx.amount} ${tx.symbol || tx.asset_type || 'ETH'}`,
            amount: tx.amount,
            asset: tx.symbol || tx.asset_type || 'ETH',
            hash: tx.hash
          }
        });
      });
    });

    // Initialize Cytoscape Instance
    const cy = cytoscape({
      container: containerRef.current,
      elements: elements,
      boxSelectionEnabled: false,
      autounselectify: false,
      style: [
        {
          selector: 'node',
          style: {
            'label': 'data(label)',
            'color': '#f8fafc',
            'font-size': '11px',
            'font-family': 'monospace',
            'text-valign': 'bottom',
            'text-margin-y': 6,
            'background-color': (node) => {
              const type = node.data('entityType').toUpperCase();
              if (type.includes('MIXER')) return '#ef4444';
              if (type.includes('VASP') || type.includes('EXCHANGE')) return '#3b82f6';
              if (type.includes('BRIDGE')) return '#f59e0b';
              if (type.includes('SCAM') || type.includes('FRAUD')) return '#a855f7';
              return '#64748b';
            },
            'border-width': (node) => (node.data('isTarget') ? 4 : 2),
            'border-color': (node) => (node.data('isTarget') ? '#00f0ff' : '#1e293b'),
            'width': (node) => (node.data('isTarget') ? 42 : 34),
            'height': (node) => (node.data('isTarget') ? 42 : 34),
            'transition-property': 'background-color, border-color, width, height',
            'transition-duration': '0.2s'
          }
        },
        {
          selector: 'node:selected',
          style: {
            'border-width': 4,
            'border-color': '#00f0ff',
            'shadow-blur': 12,
            'shadow-color': '#00f0ff'
          }
        },
        {
          selector: 'edge',
          style: {
            'width': 2,
            'line-color': '#334155',
            'target-arrow-color': '#64748b',
            'target-arrow-shape': 'triangle',
            'curve-style': 'bezier',
            'label': 'data(label)',
            'font-size': '9px',
            'color': '#94a3b8',
            'text-background-opacity': 0.8,
            'text-background-color': '#0a0e17',
            'text-background-padding': '3px',
            'text-background-shape': 'roundrectangle'
          }
        }
      ],
      layout: {
        name: 'dagre',
        rankDir: 'LR',
        nodeSep: 60,
        rankSep: 100,
        animate: true,
        animationDuration: 500
      }
    });

    // Handle node selection
    cy.on('tap', 'node', (evt) => {
      const node = evt.target;
      const data = node.data();
      if (onSelectNode) {
        onSelectNode(data.info || { address: data.fullAddress });
      }
    });

    cyRef.current = cy;

    return () => {
      if (cyRef.current) {
        cyRef.current.destroy();
      }
    };
  }, [traceData]);

  // Controls handlers
  const handleZoomIn = () => cyRef.current && cyRef.current.zoom(cyRef.current.zoom() * 1.25);
  const handleZoomOut = () => cyRef.current && cyRef.current.zoom(cyRef.current.zoom() * 0.8);
  const handleFit = () => cyRef.current && cyRef.current.fit(padding = 50);
  const handleResetLayout = () => {
    if (cyRef.current) {
      cyRef.current.layout({ name: 'dagre', rankDir: 'LR', animate: true }).run();
    }
  };

  return (
    <div className="relative w-full h-full min-h-[500px] glass-panel rounded-xl overflow-hidden border border-slate-800">
      {/* Cytoscape Canvas Container */}
      <div ref={containerRef} className="cytoscape-container" />

      {/* Floating Graph Controls */}
      <div className="absolute top-4 right-4 flex flex-col gap-2 z-10">
        <button
          onClick={handleZoomIn}
          title="Zoom In"
          className="p-2 rounded-lg bg-slate-900/90 text-slate-300 hover:text-cyan-400 border border-slate-700/60 shadow-lg transition"
        >
          <ZoomIn className="w-4 h-4" />
        </button>
        <button
          onClick={handleZoomOut}
          title="Zoom Out"
          className="p-2 rounded-lg bg-slate-900/90 text-slate-300 hover:text-cyan-400 border border-slate-700/60 shadow-lg transition"
        >
          <ZoomOut className="w-4 h-4" />
        </button>
        <button
          onClick={handleFit}
          title="Fit Canvas"
          className="p-2 rounded-lg bg-slate-900/90 text-slate-300 hover:text-cyan-400 border border-slate-700/60 shadow-lg transition"
        >
          <Maximize2 className="w-4 h-4" />
        </button>
        <button
          onClick={handleResetLayout}
          title="Rearrange Dagre Layout"
          className="p-2 rounded-lg bg-slate-900/90 text-slate-300 hover:text-cyan-400 border border-slate-700/60 shadow-lg transition"
        >
          <RefreshCw className="w-4 h-4" />
        </button>
      </div>

      {/* Graph Legend Overlay */}
      <div className="absolute bottom-4 left-4 z-10 glass-card p-3 rounded-lg border border-slate-800 flex items-center gap-4 text-xs">
        <span className="font-semibold text-slate-400">Legend:</span>
        <div className="flex items-center gap-1.5"><span className="w-2.5 h-2.5 rounded-full bg-red-500"></span><span className="text-slate-300">Mixer</span></div>
        <div className="flex items-center gap-1.5"><span className="w-2.5 h-2.5 rounded-full bg-blue-500"></span><span className="text-slate-300">VASP</span></div>
        <div className="flex items-center gap-1.5"><span className="w-2.5 h-2.5 rounded-full bg-amber-500"></span><span className="text-slate-300">Bridge</span></div>
        <div className="flex items-center gap-1.5"><span className="w-2.5 h-2.5 rounded-full bg-purple-500"></span><span className="text-slate-300">Scam</span></div>
        <div className="flex items-center gap-1.5"><span className="w-2.5 h-2.5 rounded-full bg-slate-500"></span><span className="text-slate-300">Unknown</span></div>
      </div>
    </div>
  );
}
