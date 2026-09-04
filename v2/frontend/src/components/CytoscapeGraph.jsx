import React, { useEffect, useRef } from 'react';
import cytoscape from 'cytoscape';
import { ZoomIn, ZoomOut, RefreshCw, Crosshair } from 'lucide-react';
import { shortenAddress, formatAmount } from '../utils/formatters';

const TARGET_NODE_SIZE = 70;
const OTHER_NODE_SIZE = 36;
const MIN_H_SPACING = 120;
const MIN_V_SPACING = 100;
const LAYER_GAP = 70;
const PADDING = 80;
const MIN_ZOOM = 0.12;
const MAX_ZOOM = 3;

const ENTITY_COLOR = (type) => {
  const t = (type || 'Unknown').toUpperCase();
  if (t.includes('MIXER')) return '#ef4444';
  if (t.includes('VASP') || t.includes('EXCHANGE')) return '#3b82f6';
  if (t.includes('BRIDGE')) return '#f59e0b';
  if (t.includes('SCAM') || t.includes('FRAUD')) return '#a855f7';
  return '#64748b';
};

function shortenNodeLabel(node) {
  if (!node) return '';
  if (node.entity && node.entity !== 'Unknown') return node.entity;
  const a = node.address || '';
  if (!a.startsWith('0x')) return shortenAddress(a, 6, 4);
  return `${a.slice(0, 6)}…${a.slice(-4)}`;
}

function buildElements(traceData) {
  const elements = [];
  const nodeMap = new Map();
  const targetLower = (traceData.target_address || '').toLowerCase();

  const discoveredList = traceData.trace_results?.discovered_addresses || [];
  discoveredList.forEach((nodeInfo) => {
    if (nodeInfo?.address) nodeMap.set(nodeInfo.address.toLowerCase(), nodeInfo);
  });

  const getNodeInfo = (addr) => {
    const lower = addr.toLowerCase();
    if (nodeMap.has(lower)) return nodeMap.get(lower);
    return {
      address: addr,
      entity: 'Unknown',
      entity_type: 'Unknown',
      hop_distance: 0,
      risk: { score: 0, risk_level: 'Low' },
    };
  };

  const addedNodeIds = new Set();
  const ensureNode = (addr) => {
    const lower = (addr || '').toLowerCase();
    if (!lower) return null;
    if (addedNodeIds.has(lower)) return lower;
    addedNodeIds.add(lower);

    const info = getNodeInfo(addr);
    const isTarget = lower === targetLower;
    const entityType = info.entity_type || 'Unknown';
    const hop = info.hop_distance ?? 0;

    elements.push({
      group: 'nodes',
      data: {
        id: lower,
        label: isTarget ? '★ TARGET ★' : shortenNodeLabel(info),
        fullAddress: addr,
        entity: info.entity,
        entityType: entityType,
        hopDistance: hop,
        riskScore: info.risk?.score || 0,
        riskLevel: info.risk?.risk_level || 'Low',
        isTarget,
        info,
      },
      classes: isTarget ? 'isTarget' : '',
    });
    return lower;
  };

  const edgeAgg = new Map();
  Object.entries(traceData.graph || {}).forEach(([sourceAddr, txList]) => {
    const sourceId = ensureNode(sourceAddr);
    if (!sourceId) return;
    (txList || []).forEach((tx) => {
      const toAddr = tx?.to;
      if (!toAddr) return;
      const targetId = ensureNode(toAddr);
      if (!targetId || sourceId === targetId) return;

      const key = `${sourceId}->${targetId}`;
      let entry = edgeAgg.get(key);
      if (!entry) {
        entry = {
          id: key,
          source: sourceId,
          target: targetId,
          txCount: 0,
          totalAmount: 0,
          representativeAmount: 0,
          representativeAsset: 'ETH',
          assets: new Set(),
          hashes: [],
          largestAmount: 0,
        };
        edgeAgg.set(key, entry);
      }
      const amt = parseFloat(tx.amount);
      if (Number.isFinite(amt) && amt > 0) {
        entry.totalAmount += amt;
        if (amt > entry.largestAmount) {
          entry.largestAmount = amt;
          entry.representativeAmount = amt;
          entry.representativeAsset = tx.symbol || tx.asset_type || 'ETH';
        }
      }
      entry.txCount += 1;
      if (tx.symbol || tx.asset_type) entry.assets.add(tx.symbol || tx.asset_type);
      if (tx.hash) entry.hashes.push(tx.hash);
    });
  });

  edgeAgg.forEach((entry) => {
    elements.push({
      group: 'edges',
      data: {
        id: entry.id,
        source: entry.source,
        target: entry.target,
        label: entry.txCount > 1
          ? `${formatAmount(entry.representativeAmount, entry.representativeAsset)} × ${entry.txCount}`
          : formatAmount(entry.representativeAmount, entry.representativeAsset),
        txCount: entry.txCount,
        totalAmount: entry.totalAmount,
        representativeAmount: entry.representativeAmount,
        representativeAsset: entry.representativeAsset,
        assets: Array.from(entry.assets),
        hashes: entry.hashes.slice(0, 5),
        hashCount: entry.hashes.length,
      },
    });
  });

  return { elements, targetId: targetLower };
}

// Directed BFS backwards from the target (following edges toward the target).
function computeHopDistancesToTarget(elements, targetId) {
  const rev = new Map();
  const nodes = new Set();
  elements.forEach((e) => {
    if (e.group === 'nodes') nodes.add(e.data.id);
    if (e.group === 'edges') {
      const s = e.data.source.toLowerCase();
      const t = e.data.target.toLowerCase();
      if (!rev.has(t)) rev.set(t, []);
      rev.get(t).push(s);
    }
  });

  const hops = new Map();
  if (!nodes.has(targetId)) return hops;
  hops.set(targetId, 0);
  const queue = [targetId];
  while (queue.length) {
    const node = queue.shift();
    const h = hops.get(node);
    for (const n of rev.get(node) || []) {
      if (!hops.has(n)) {
        hops.set(n, h + 1);
        queue.push(n);
      }
    }
  }
  return hops;
}

// Undirected fallback for nodes the directed BFS couldn't reach.
function fillUnreachableWithUndirectedHops(elements, hops, targetId) {
  if (!hops.has(targetId)) return hops;
  const maxKnown = Math.max(0, ...Array.from(hops.values()));
  const adj = new Map();
  elements.forEach((e) => {
    if (e.group !== 'edges') return;
    const s = e.data.source.toLowerCase();
    const t = e.data.target.toLowerCase();
    if (!adj.has(s)) adj.set(s, []);
    if (!adj.has(t)) adj.set(t, []);
    adj.get(s).push(t);
    adj.get(t).push(s);
  });
  const visited = new Set(hops.keys());
  const queue = [...hops.keys()];
  while (queue.length) {
    const node = queue.shift();
    const h = hops.get(node);
    const neighbours = adj.get(node) || [];
    for (const n of neighbours) {
      if (!visited.has(n)) {
        visited.add(n);
        hops.set(n, Math.min(h + 1, maxKnown + 1));
        queue.push(n);
      }
    }
  }
  return hops;
}

function groupByHop(elements, targetId) {
  const hops = fillUnreachableWithUndirectedHops(
    elements,
    computeHopDistancesToTarget(elements, targetId),
    targetId,
  );

  const out = new Map();
  elements.forEach((e) => {
    if (e.group !== 'nodes') return;
    if (e.data.isHopLabel) return;
    const id = e.data.id;
    if (id === targetId) return;
    const h = hops.has(id) ? hops.get(id) : 1;
    if (!out.has(h)) out.set(h, []);
    out.get(h).push(id);
  });
  return out;
}

function placeRowGrid(positions, nodes, cols, spacing, firstRowY, rowHeight) {
  const sign = firstRowY < 0 ? -1 : 1;
  nodes.forEach((id, i) => {
    const col = i % cols;
    const row = Math.floor(i / cols);
    const nodesInRow = Math.min(cols, nodes.length - row * cols);
    const rowWidth = (nodesInRow - 1) * spacing;
    const x = -rowWidth / 2 + col * spacing;
    const y = firstRowY + sign * row * rowHeight;
    positions[id] = { x, y };
  });
}

function computeBBox(positions, elements) {
  let minX = Infinity;
  let maxX = -Infinity;
  let minY = Infinity;
  let maxY = -Infinity;

  elements.forEach((e) => {
    if (e.group !== 'nodes') return;
    const p = positions[e.data.id];
    if (!p) return;

    let r = OTHER_NODE_SIZE / 2;
    if (e.data.isTarget) r = TARGET_NODE_SIZE / 2;
    else if (e.data.isHopLabel) r = 0;

    minX = Math.min(minX, p.x - r);
    maxX = Math.max(maxX, p.x + r);
    minY = Math.min(minY, p.y - r);
    maxY = Math.max(maxY, p.y + r);
  });

  if (!Number.isFinite(minX)) return { x: 0, y: 0, w: 0, h: 0 };
  return { x: minX, y: minY, w: maxX - minX, h: maxY - minY };
}

// Deterministic layered layout: target at the origin, each hop placed in
// clearly separated horizontal bands above and below the target.  Multiple
// rows are used automatically when a hop has more nodes than fit across the
// available width.
function layeredLayoutPositions(elements, targetId, containerDims) {
  const byHop = groupByHop(elements, targetId);

  const W = Math.max(containerDims.width || 0, 640);
  const H = Math.max(containerDims.height || 0, 480);
  const usableW = Math.max(MIN_H_SPACING, W - 2 * PADDING);

  const positions = {};
  if (targetId) positions[targetId] = { x: 0, y: 0 };

  const cols = Math.max(1, Math.floor(usableW / MIN_H_SPACING));

  const activeHops = [...byHop.keys()]
    .filter((h) => (byHop.get(h) || []).length > 0)
    .sort((a, b) => a - b);

  const halfNode = OTHER_NODE_SIZE / 2;
  const targetHalf = TARGET_NODE_SIZE / 2;
  let currentOffset = targetHalf + LAYER_GAP + halfNode;

  const labelNodes = [];

  activeHops.forEach((hop) => {
    const nodes = byHop.get(hop).slice().sort();
    const N = nodes.length;
    const topN = Math.ceil(N / 2);
    const botN = N - topN;

    const topRows = Math.max(1, Math.ceil(topN / cols));
    const botRows = Math.max(1, Math.ceil(botN / cols));
    const rows = Math.max(topRows, botRows);

    placeRowGrid(positions, nodes.slice(0, topN), cols, MIN_H_SPACING, -currentOffset, MIN_V_SPACING);
    placeRowGrid(positions, nodes.slice(topN), cols, MIN_H_SPACING, currentOffset, MIN_V_SPACING);

    const labelY = -(currentOffset - halfNode - LAYER_GAP / 2);
    const labelTop = `hop-label-${hop}-top`;
    const labelBot = `hop-label-${hop}-bottom`;
    const label = `──── HOP ${hop} ────`;

    labelNodes.push({
      group: 'nodes',
      data: { id: labelTop, label, isHopLabel: true },
      grabbable: false,
      selectable: false,
      classes: 'hopLabel',
    });
    labelNodes.push({
      group: 'nodes',
      data: { id: labelBot, label, isHopLabel: true },
      grabbable: false,
      selectable: false,
      classes: 'hopLabel',
    });

    positions[labelTop] = { x: 0, y: labelY };
    positions[labelBot] = { x: 0, y: -labelY };

    currentOffset += (rows - 1) * MIN_V_SPACING + OTHER_NODE_SIZE + LAYER_GAP;
  });

  const augmentedElements = [...elements, ...labelNodes];
  const bbox = computeBBox(positions, augmentedElements);

  return { positions, bbox, targetId, elements: augmentedElements, realElements: elements };
}

function fitCamera(cy, container, layoutInfo) {
  if (!cy || cy.destroyed() || !container || !layoutInfo) return;

  const targetNode = cy.nodes('.isTarget').first();
  if (targetNode && targetNode.length) targetNode.position({ x: 0, y: 0 });

  const W = Math.max(container.clientWidth || 0, 320);
  const H = Math.max(container.clientHeight || 0, 320);
  const bbox = layoutInfo.bbox || { x: 0, y: 0, w: 0, h: 0 };

  const requiredW = bbox.w + 2 * PADDING;
  const requiredH = bbox.h + 2 * PADDING;
  const zoom = Math.max(MIN_ZOOM, Math.min(MAX_ZOOM, Math.min(W / requiredW, H / requiredH)));

  cy.zoom(zoom);
  cy.pan({ x: W / 2, y: H / 2 });
}

export default function CytoscapeGraph({ traceData, selectedNode, onSelectNode }) {
  const containerRef = useRef(null);
  const cyRef = useRef(null);
  const selectedNodeIdRef = useRef(null);
  const layoutInfoRef = useRef(null);

  const applyHighlight = (cy, idOrNull) => {
    if (!cy || cy.destroyed()) return;
    cy.elements().removeClass('faded highlighted edge-hot edge-hover');
    if (!idOrNull) return;
    const node = cy.getElementById(idOrNull);
    if (!node || !node.length) return;
    const neighborhood = node.closedNeighborhood();
    cy.elements().not(neighborhood).not('.hopLabel').addClass('faded');
    neighborhood.addClass('highlighted');
    node.connectedEdges().addClass('edge-hot');
  };

  useEffect(() => {
    if (!containerRef.current || !traceData || !traceData.graph) return;

    const container = containerRef.current;
    const dims = {
      width: container.clientWidth || 0,
      height: container.clientHeight || 0,
    };

    const { elements, targetId } = buildElements(traceData);
    const targetExists = targetId && elements.some(
      (e) => e.group === 'nodes' && e.data.id === targetId,
    );
    if (!targetExists) {
      // eslint-disable-next-line no-console
      console.warn('[CytoscapeGraph] target_address not found in trace graph; rendering without a fixed centre.');
    }

    const layoutInfo = layeredLayoutPositions(elements, targetId, dims);
    layoutInfo.targetId = targetExists ? targetId : null;
    layoutInfoRef.current = layoutInfo;

    const cy = cytoscape({
      container: containerRef.current,
      elements: layoutInfo.elements,
      boxSelectionEnabled: false,
      autounselectify: false,
      wheelSensitivity: 0.25,
      minZoom: MIN_ZOOM,
      maxZoom: MAX_ZOOM,
      style: [
        {
          selector: 'node',
          style: {
            label: 'data(label)',
            color: '#f8fafc',
            'font-size': '10px',
            'font-family': 'monospace',
            'font-weight': 600,
            'text-valign': 'bottom',
            'text-halign': 'center',
            'text-margin-y': 10,
            'text-background-opacity': 0.9,
            'text-background-color': '#0a0e17',
            'text-background-padding': '4px',
            'text-background-shape': 'roundrectangle',
            'background-color': (node) => ENTITY_COLOR(node.data('entityType')),
            'border-width': 2,
            'border-color': '#1e293b',
            width: OTHER_NODE_SIZE,
            height: OTHER_NODE_SIZE,
            'overlay-opacity': 0,
            'transition-property': 'background-color, border-color, opacity, width, height',
            'transition-duration': '0.2s',
            'z-index': 1,
          },
        },
        {
          selector: 'node.isTarget',
          style: {
            'background-color': '#00f0ff',
            'background-blacken': -0.15,
            'border-color': '#a5f3fc',
            'border-width': 5,
            width: TARGET_NODE_SIZE,
            height: TARGET_NODE_SIZE,
            'font-size': '13px',
            'font-weight': 'bold',
            color: '#00f0ff',
            'text-valign': 'top',
            'text-halign': 'center',
            'text-margin-y': -14,
            'text-background-color': '#0a0e17',
            'text-background-opacity': 1,
            'text-background-padding': '6px',
            'text-background-shape': 'roundrectangle',
            'outline-color': '#00f0ff',
            'outline-width': 3,
            'outline-opacity': 0.6,
            'shadow-blur': 30,
            'shadow-color': '#00f0ff',
            'shadow-opacity': 0.95,
            'shadow-offset-x': 0,
            'shadow-offset-y': 0,
            'z-index': 999,
          },
        },
        {
          selector: 'node.hopLabel',
          style: {
            label: 'data(label)',
            color: '#64748b',
            'font-size': '10px',
            'font-family': 'monospace',
            'font-weight': 600,
            'text-valign': 'center',
            'text-halign': 'center',
            'text-background-opacity': 0,
            'background-opacity': 0,
            'border-width': 0,
            width: 1,
            height: 1,
            'overlay-opacity': 0,
            'z-index': 0,
            events: 'no',
          },
        },
        {
          selector: 'node.faded',
          style: {
            opacity: 0.18,
            'text-opacity': 0.2,
          },
        },
        {
          selector: 'node.highlighted',
          style: {
            'border-width': 4,
            'border-color': '#00f0ff',
            'shadow-blur': 14,
            'shadow-color': '#00f0ff',
            'shadow-opacity': 0.95,
            'z-index': 50,
          },
        },
        {
          selector: 'node:selected',
          style: {
            'border-width': 4,
            'border-color': '#00f0ff',
            'shadow-blur': 14,
            'shadow-color': '#00f0ff',
            'shadow-opacity': 0.9,
          },
        },
        {
          selector: 'edge',
          style: {
            width: 1.2,
            'line-color': '#3b4a63',
            'target-arrow-color': '#64748b',
            'target-arrow-shape': 'triangle',
            'curve-style': 'bezier',
            'control-point-step-size': 24,
            label: '',
            'font-size': '10px',
            color: '#e2e8f0',
            'text-background-opacity': 0.95,
            'text-background-color': '#0a0e17',
            'text-background-padding': '4px',
            'text-background-shape': 'roundrectangle',
            opacity: 0.5,
            'arrow-scale': 0.85,
            'transition-property': 'line-color, target-arrow-color, opacity, width',
            'transition-duration': '0.2s',
            'z-index': 1,
          },
        },
        {
          selector: 'edge.faded',
          style: {
            opacity: 0.05,
          },
        },
        {
          selector: 'edge.edge-hot',
          style: {
            label: 'data(label)',
            'line-color': '#00f0ff',
            'target-arrow-color': '#00f0ff',
            width: 2.6,
            opacity: 1,
            'z-index': 60,
          },
        },
        {
          selector: 'edge.edge-hover',
          style: {
            label: 'data(label)',
            'line-color': '#00f0ff',
            'target-arrow-color': '#00f0ff',
            width: 2.2,
            opacity: 1,
            'z-index': 60,
          },
        },
        {
          selector: 'edge:selected, edge.highlighted',
          style: {
            label: 'data(label)',
            'line-color': '#00f0ff',
            'target-arrow-color': '#00f0ff',
            width: 2.6,
            opacity: 1,
            'z-index': 60,
          },
        },
      ],
    });

    cy.layout({
      name: 'preset',
      positions: layoutInfo.positions,
      animate: true,
      animationDuration: 600,
      animationEasing: 'ease-out',
      fit: false,
      padding: 0,
    }).run();

    const frameToContainer = () => {
      if (!cy || cy.destroyed() || !containerRef.current) return;
      try { cy.resize(); } catch (_) {}
      const targetNode = cy.nodes('.isTarget').first();
      if (targetNode && targetNode.length) targetNode.position({ x: 0, y: 0 });
      fitCamera(cy, containerRef.current, layoutInfoRef.current);
    };
    [60, 250, 700, 1300].forEach((ms) => setTimeout(frameToContainer, ms));

    cy.on('tap', 'node', (evt) => {
      const node = evt.target;
      const data = node.data();
      selectedNodeIdRef.current = data.id;
      if (onSelectNode) onSelectNode(data.info || { address: data.fullAddress });
      applyHighlight(cy, data.id);
    });

    cy.on('tap', 'edge', (evt) => {
      const edge = evt.target;
      cy.elements().unselect();
      edge.select();
    });

    cy.on('mouseover', 'edge', (evt) => {
      evt.target.addClass('edge-hover');
    });

    cy.on('mouseout', 'edge', (evt) => {
      const edge = evt.target;
      if (!edge.selected()) edge.removeClass('edge-hover');
    });

    cy.on('tap', (evt) => {
      if (evt.target === cy) {
        selectedNodeIdRef.current = null;
        applyHighlight(cy, null);
      }
    });

    const handleResize = () => frameToContainer();
    window.addEventListener('resize', handleResize);
    const ro = (typeof ResizeObserver !== 'undefined') ? new ResizeObserver(handleResize) : null;
    if (ro && containerRef.current) ro.observe(containerRef.current);

    cyRef.current = cy;

    return () => {
      window.removeEventListener('resize', handleResize);
      if (ro) ro.disconnect();
      if (cyRef.current && !cyRef.current.destroyed()) {
        cyRef.current.destroy();
      }
      cyRef.current = null;
    };
  }, [traceData]);

  useEffect(() => {
    const cy = cyRef.current;
    if (!cy || cy.destroyed()) return;
    const wantId = selectedNode?.address ? selectedNode.address.toLowerCase() : null;
    if (!wantId) {
      selectedNodeIdRef.current = null;
      applyHighlight(cy, null);
      return;
    }
    if (selectedNodeIdRef.current === wantId) return;
    const node = cy.getElementById(wantId);
    if (node && node.length) {
      cy.elements().unselect();
      node.select();
      selectedNodeIdRef.current = wantId;
      applyHighlight(cy, wantId);
    }
  }, [selectedNode]);

  const handleZoomIn = () => cyRef.current && !cyRef.current.destroyed() &&
    cyRef.current.zoom({ level: cyRef.current.zoom() * 1.25, renderedPosition: { x: cyRef.current.width() / 2, y: cyRef.current.height() / 2 } });
  const handleZoomOut = () => cyRef.current && !cyRef.current.destroyed() &&
    cyRef.current.zoom({ level: cyRef.current.zoom() * 0.8, renderedPosition: { x: cyRef.current.width() / 2, y: cyRef.current.height() / 2 } });
  const handleFit = () => {
    if (!cyRef.current || cyRef.current.destroyed() || !containerRef.current) return;
    fitCamera(cyRef.current, containerRef.current, layoutInfoRef.current);
  };

  const handleAutoArrange = () => {
    const cy = cyRef.current;
    if (!cy || cy.destroyed() || !containerRef.current) return;
    const ref = layoutInfoRef.current;
    if (!ref || !ref.realElements) return;
    const dims = {
      width: containerRef.current.clientWidth || 0,
      height: containerRef.current.clientHeight || 0,
    };
    const rebuilt = layeredLayoutPositions(ref.realElements, ref.targetId, dims);
    rebuilt.targetId = ref.targetId;
    layoutInfoRef.current = rebuilt;
    cy.layout({
      name: 'preset',
      positions: rebuilt.positions,
      animate: true,
      animationDuration: 600,
      animationEasing: 'ease-out',
      fit: false,
      padding: 0,
    }).run();
    setTimeout(() => {
      if (!cy.destroyed() && containerRef.current) {
        fitCamera(cy, containerRef.current, layoutInfoRef.current);
      }
    }, 700);
  };

  const handleResetLayout = handleAutoArrange;

  return (
    <div className="relative w-full h-full min-h-[500px] glass-panel rounded-xl overflow-hidden border border-slate-800">
      <div ref={containerRef} className="cytoscape-container w-full h-full" />

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
          title="Centre Target"
          className="p-2 rounded-lg bg-slate-900/90 text-slate-300 hover:text-cyan-400 border border-slate-700/60 shadow-lg transition"
        >
          <Crosshair className="w-4 h-4" />
        </button>
        <button
          onClick={handleAutoArrange}
          title="Re-layout / Auto Arrange"
          className="p-2 rounded-lg bg-cyan-500/15 text-cyan-300 hover:text-cyan-200 hover:bg-cyan-500/25 border border-cyan-500/40 shadow-lg transition"
        >
          <RefreshCw className="w-4 h-4" />
        </button>
      </div>

      <div className="absolute bottom-4 left-4 z-10 glass-card p-3 rounded-lg border border-slate-800 flex flex-col gap-2 text-xs">
        <div className="flex items-center gap-3 flex-wrap">
          <span className="font-bold text-cyan-400">Layered Investigation Map</span>
          <div className="flex items-center gap-1.5">
            <span className="w-3 h-3 rounded-full bg-cyan-400 shadow shadow-cyan-400/60"></span>
            <span className="text-slate-300">★ Target (centre)</span>
          </div>
          <div className="flex items-center gap-1.5"><span className="w-2.5 h-2.5 rounded-full bg-red-500"></span><span className="text-slate-300">Mixer</span></div>
          <div className="flex items-center gap-1.5"><span className="w-2.5 h-2.5 rounded-full bg-blue-500"></span><span className="text-slate-300">VASP</span></div>
          <div className="flex items-center gap-1.5"><span className="w-2.5 h-2.5 rounded-full bg-amber-500"></span><span className="text-slate-300">Bridge</span></div>
          <div className="flex items-center gap-1.5"><span className="w-2.5 h-2.5 rounded-full bg-purple-500"></span><span className="text-slate-300">Scam</span></div>
          <div className="flex items-center gap-1.5"><span className="w-2.5 h-2.5 rounded-full bg-slate-500"></span><span className="text-slate-300">Unknown</span></div>
        </div>
        <div className="text-[10px] text-slate-400 flex items-center gap-2 flex-wrap">
          <span>Target = exact centre · Hop bands expand outward · Multiple rows per hop when dense · Click a node to highlight its neighbourhood</span>
        </div>
      </div>
    </div>
  );
}
