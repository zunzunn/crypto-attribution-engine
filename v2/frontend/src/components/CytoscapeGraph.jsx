import React, { useEffect, useRef, useState } from 'react';
import cytoscape from 'cytoscape';
import GraphToolbar from './investigation/GraphToolbar';
import { shortenAddress, formatAmount, getEntityColor } from '../utils/formatters';

const TARGET_NODE_SIZE = 72;
const OTHER_NODE_SIZE = 38;
const MIN_H_SPACING = 130;
const MIN_V_SPACING = 110;
const LAYER_GAP = 75;
const PADDING = 90;
const MIN_ZOOM = 0.12;
const MAX_ZOOM = 3.5;

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
    targetId
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

function layeredLayoutPositions(elements, targetId, containerDims) {
  const byHop = groupByHop(elements, targetId);

  const W = Math.max(containerDims.width || 0, 640);
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
    const riskLevel = info.risk?.risk_level || 'Low';
    const isUnknown = !info.entity || info.entity === 'Unknown';

    let displayLabel = isTarget
      ? 'TARGET WALLET'
      : isUnknown
      ? shortenAddress(addr, 6, 4)
      : info.entity;

    elements.push({
      group: 'nodes',
      data: {
        id: lower,
        label: displayLabel,
        fullAddress: addr,
        entity: info.entity,
        entityType: entityType,
        hopDistance: hop,
        riskScore: info.risk?.score ?? 0,
        riskLevel: riskLevel,
        confidence: info.confidence ?? 0,
        sources: info.sources || [],
        evidence: info.evidence ?? '',
        riskReasons: info.risk?.reasons || [],
        isTarget,
        isUnknown,
        info,
      },
      classes: `${isTarget ? 'isTarget' : ''} ${isUnknown ? 'isUnknown' : 'isAttributed'} risk-${riskLevel.toLowerCase()}`,
    });
    return lower;
  };

  const edgeAgg = new Map();
  Object.entries(traceData.graph || {}).forEach(([sourceAddr, txList]) => {
    const sourceId = ensureNode(sourceAddr);
    if (!sourceId) return;
    (txList || []).forEach((tx) => {
      const toAddr = tx?.to || tx?.to_address;
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
    const labelText = entry.txCount > 1
      ? `${formatAmount(entry.representativeAmount, entry.representativeAsset)} (x${entry.txCount})`
      : formatAmount(entry.representativeAmount, entry.representativeAsset);

    elements.push({
      group: 'edges',
      data: {
        id: entry.id,
        source: entry.source,
        target: entry.target,
        label: labelText,
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

export default function CytoscapeGraph({
  traceData,
  selectedNode,
  onSelectNode,
  filterSearch = '',
  selectedEntities = ['VASP', 'MIXER', 'BRIDGE', 'SCAM', 'UNKNOWN'],
  selectedRisks = ['Critical', 'High', 'Medium', 'Low'],
  selectedHops = [0, 1, 2, 3]
}) {
  const containerRef = useRef(null);
  const cyRef = useRef(null);
  const selectedNodeIdRef = useRef(null);
  const layoutInfoRef = useRef(null);
  const [showEdgeLabels, setShowEdgeLabels] = useState(false);
  const onSelectNodeRef = useRef(onSelectNode);

  useEffect(() => {
    onSelectNodeRef.current = onSelectNode;
  }, [onSelectNode]);

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
    const layoutInfo = layeredLayoutPositions(elements, targetId, dims);
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
            color: '#cbd5e1',
            'font-size': '10px',
            'font-family': 'monospace',
            'font-weight': 600,
            'text-valign': 'bottom',
            'text-halign': 'center',
            'text-margin-y': 7,
            'text-background-opacity': 0.85,
            'text-background-color': '#070b14',
            'text-background-padding': '3px',
            'text-background-shape': 'roundrectangle',
            'background-color': '#1e293b',
            'border-width': 2,
            'border-color': '#334155',
            width: OTHER_NODE_SIZE,
            height: OTHER_NODE_SIZE,
            'transition-property': 'background-color, border-color, opacity, width, height',
            'transition-duration': '0.2s',
            'z-index': 2,
          },
        },
        {
          selector: 'node.isAttributed',
          style: {
            'background-color': (n) => getEntityColor(n.data('entityType')),
            'border-width': 2.5,
            'border-color': '#0f172a',
          },
        },
        {
          selector: 'node.isUnknown',
          style: {
            'background-color': '#0f172a',
            'border-width': 2,
            'border-color': '#475569',
            'border-style': 'dashed',
            color: '#94a3b8',
          },
        },
        {
          selector: 'node.risk-critical',
          style: {
            'border-color': '#ef4444',
            'border-width': 3.5,
            'shadow-blur': 12,
            'shadow-color': '#ef4444',
            'shadow-opacity': 0.6,
          },
        },
        {
          selector: 'node.risk-high',
          style: {
            'border-color': '#f43f5e',
            'border-width': 3,
            'shadow-blur': 8,
            'shadow-color': '#f43f5e',
            'shadow-opacity': 0.5,
          },
        },
        {
          selector: 'node.risk-medium',
          style: {
            'border-color': '#f59e0b',
            'border-width': 2.5,
          },
        },
        {
          selector: 'node.isTarget',
          style: {
            'background-color': '#00f0ff',
            'border-color': '#ffffff',
            'border-width': 5,
            width: TARGET_NODE_SIZE,
            height: TARGET_NODE_SIZE,
            'font-size': '12px',
            'font-weight': 'bold',
            color: '#00f0ff',
            'text-valign': 'top',
            'text-halign': 'center',
            'text-margin-y': -12,
            'text-background-color': '#070b14',
            'text-background-opacity': 1,
            'text-background-padding': '5px',
            'text-background-shape': 'roundrectangle',
            'shadow-blur': 25,
            'shadow-color': '#00f0ff',
            'shadow-opacity': 0.9,
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
            'z-index': 0,
            events: 'no',
          },
        },
        {
          selector: 'node.faded',
          style: {
            opacity: 0.15,
            'text-opacity': 0.15,
          },
        },
        {
          selector: 'node.highlighted',
          style: {
            'border-width': 4,
            'border-color': '#00f0ff',
            'shadow-blur': 16,
            'shadow-color': '#00f0ff',
            'shadow-opacity': 0.9,
            'z-index': 80,
          },
        },
        {
          selector: 'node:selected',
          style: {
            'border-width': 4,
            'border-color': '#00f0ff',
            'shadow-blur': 16,
            'shadow-color': '#00f0ff',
            'shadow-opacity': 0.9,
          },
        },
        {
          selector: 'edge',
          style: {
            width: 1.3,
            'line-color': '#2a3b5c',
            'target-arrow-color': '#475569',
            'target-arrow-shape': 'triangle',
            'curve-style': 'bezier',
            label: '',
            'font-size': '10px',
            'font-family': 'monospace',
            color: '#e2e8f0',
            'text-background-opacity': 0.9,
            'text-background-color': '#070b14',
            'text-background-padding': '3px',
            'text-background-shape': 'roundrectangle',
            opacity: 0.55,
            'arrow-scale': 0.85,
            'transition-property': 'line-color, target-arrow-color, opacity, width',
            'transition-duration': '0.2s',
            'z-index': 1,
          },
        },
        {
          selector: 'edge.showLabels',
          style: {
            label: 'data(label)',
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
            width: 2.8,
            opacity: 1,
            'z-index': 70,
          },
        },
        {
          selector: 'edge.edge-hover',
          style: {
            label: 'data(label)',
            'line-color': '#00f0ff',
            'target-arrow-color': '#00f0ff',
            width: 2.4,
            opacity: 1,
            'z-index': 70,
          },
        },
      ],
    });

    cy.layout({
      name: 'preset',
      positions: layoutInfo.positions,
      animate: true,
      animationDuration: 600,
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

    [60, 300, 800].forEach((ms) => setTimeout(frameToContainer, ms));

    cy.on('tap', 'node', (evt) => {
      const node = evt.target;
      const data = node.data();
      if (data.isHopLabel) return;
      selectedNodeIdRef.current = data.id;
      if (onSelectNodeRef.current) onSelectNodeRef.current(data.info || { address: data.fullAddress });
      applyHighlight(cy, data.id);
    });

    cy.on('mouseover', 'edge', (evt) => {
      evt.target.addClass('edge-hover');
    });

    cy.on('mouseout', 'edge', (evt) => {
      const edge = evt.target;
      if (!edge.hasClass('edge-hot')) edge.removeClass('edge-hover');
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

  // Sync selected node with prop
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

  // Sync edge labels toggle
  useEffect(() => {
    const cy = cyRef.current;
    if (!cy || cy.destroyed()) return;
    if (showEdgeLabels) {
      cy.edges().addClass('showLabels');
    } else {
      cy.edges().removeClass('showLabels');
    }
  }, [showEdgeLabels]);

  // Apply filters
  useEffect(() => {
    const cy = cyRef.current;
    if (!cy || cy.destroyed()) return;

    cy.nodes().each((node) => {
      if (node.hasClass('hopLabel') || node.hasClass('isTarget')) return;

      const data = node.data();
      const entityType = (data.entityType || 'Unknown').toUpperCase();
      const riskLevel = data.riskLevel || 'Low';
      const hop = data.hopDistance ?? 0;
      const addr = (data.fullAddress || '').toLowerCase();
      const entName = (data.entity || '').toLowerCase();

      // Entity filter match
      let entityMatch = false;
      selectedEntities.forEach((cat) => {
        if (cat === 'UNKNOWN' && (data.isUnknown || entityType === 'UNKNOWN')) entityMatch = true;
        else if (entityType.includes(cat)) entityMatch = true;
      });

      // Risk match
      const riskMatch = selectedRisks.some(
        (r) => r.toLowerCase() === riskLevel.toLowerCase()
      );

      // Hop match
      const hopMatch = selectedHops.includes(hop);

      // Search match
      const searchMatch = !filterSearch ||
        addr.includes(filterSearch.toLowerCase()) ||
        entName.includes(filterSearch.toLowerCase());

      const shouldShow = entityMatch && riskMatch && hopMatch && searchMatch;

      if (shouldShow) {
        node.style('display', 'element');
      } else {
        node.style('display', 'none');
      }
    });

    // Hide edges where source or target is hidden
    cy.edges().each((edge) => {
      const src = edge.source();
      const tgt = edge.target();
      if (src.style('display') === 'none' || tgt.style('display') === 'none') {
        edge.style('display', 'none');
      } else {
        edge.style('display', 'element');
      }
    });
  }, [filterSearch, selectedEntities, selectedRisks, selectedHops]);

  // Toolbar Actions
  const handleZoomIn = () => {
    if (!cyRef.current || cyRef.current.destroyed()) return;
    cyRef.current.zoom({
      level: cyRef.current.zoom() * 1.25,
      renderedPosition: { x: cyRef.current.width() / 2, y: cyRef.current.height() / 2 }
    });
  };

  const handleZoomOut = () => {
    if (!cyRef.current || cyRef.current.destroyed()) return;
    cyRef.current.zoom({
      level: cyRef.current.zoom() * 0.8,
      renderedPosition: { x: cyRef.current.width() / 2, y: cyRef.current.height() / 2 }
    });
  };

  const handleFitTarget = () => {
    if (!cyRef.current || cyRef.current.destroyed() || !containerRef.current) return;
    fitCamera(cyRef.current, containerRef.current, layoutInfoRef.current);
  };

  const handleResetLayout = () => {
    const cy = cyRef.current;
    if (!cy || cy.destroyed() || !containerRef.current) return;
    const ref = layoutInfoRef.current;
    if (!ref || !ref.realElements) return;

    const dims = {
      width: containerRef.current.clientWidth || 0,
      height: containerRef.current.clientHeight || 0,
    };
    const rebuilt = layeredLayoutPositions(ref.realElements, ref.targetId, dims);
    layoutInfoRef.current = rebuilt;

    cy.layout({
      name: 'preset',
      positions: rebuilt.positions,
      animate: true,
      animationDuration: 600,
      fit: false,
      padding: 0,
    }).run();

    setTimeout(() => {
      if (!cy.destroyed() && containerRef.current) {
        fitCamera(cy, containerRef.current, layoutInfoRef.current);
      }
    }, 650);
  };

  return (
    <div className="relative w-full h-full min-h-[520px] cyber-panel rounded-xl overflow-hidden border border-slate-800/80">
      <div ref={containerRef} className="cytoscape-container w-full h-full" />

      {/* Floating Toolbar */}
      <GraphToolbar
        onZoomIn={handleZoomIn}
        onZoomOut={handleZoomOut}
        onFitTarget={handleFitTarget}
        onResetLayout={handleResetLayout}
        showEdgeLabels={showEdgeLabels}
        setShowEdgeLabels={setShowEdgeLabels}
      />

      {/* Bottom Status / Navigation Guide */}
      <div className="absolute bottom-3 left-3 z-10 cyber-panel-subtle px-3 py-1.5 rounded-lg border border-slate-800/80 flex items-center gap-3 text-[10px] font-mono text-slate-400 pointer-events-none">
        <span className="flex items-center gap-1">
          <span className="w-1.5 h-1.5 rounded-full bg-cyan-400" /> Target in center
        </span>
        <span className="hidden sm:inline">&bull;</span>
        <span className="hidden sm:inline">Click node to inspect intelligence</span>
        <span className="hidden sm:inline">&bull;</span>
        <span className="hidden sm:inline">Scroll to zoom</span>
      </div>
    </div>
  );
}
