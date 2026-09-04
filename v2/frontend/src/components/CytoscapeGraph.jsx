import React, { useEffect, useRef, useState } from 'react';
import cytoscape from 'cytoscape';
import GraphToolbar from './investigation/GraphToolbar';
import { shortenAddress, formatAmount, getEntityColor } from '../utils/formatters';

const TARGET_NODE_SIZE = 58;
const OTHER_NODE_SIZE = 42;
const MIN_H_SPACING = 170;
const LAYER_GAP = 160;
const PADDING = 60;
const MIN_ZOOM = 0.15;
const MAX_ZOOM = 2.8;

function groupByHop(elements, targetId) {
  const out = new Map();
  elements.forEach((e) => {
    if (e.group !== 'nodes' || e.data.isHopLabel) return;
    const id = e.data.id;
    if (id === targetId) return; // Target is Hop 0
    let h = e.data.hopDistance;
    if (h === undefined || h === null) h = 1;
    if (!out.has(h)) out.set(h, []);
    out.get(h).push(id);
  });
  return out;
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

  const W = Math.max(containerDims.width || 0, 750);
  const usableW = Math.max(MIN_H_SPACING * 3, W - 2 * PADDING);

  const positions = {};

  // Hop 0: Target centered at the top
  let currentY = 70;
  if (targetId) {
    positions[targetId] = { x: 0, y: currentY };
  }

  const activeHops = [...byHop.keys()]
    .filter((h) => (byHop.get(h) || []).length > 0)
    .sort((a, b) => a - b);

  activeHops.forEach((hop) => {
    const nodes = byHop.get(hop).slice();
    // Sort deterministically: highest risk first, then address
    nodes.sort((aId, bId) => {
      const aNode = elements.find((e) => e.data.id === aId);
      const bNode = elements.find((e) => e.data.id === bId);
      const aScore = aNode?.data?.riskScore || 0;
      const bScore = bNode?.data?.riskScore || 0;
      if (bScore !== aScore) return bScore - aScore;
      return aId.localeCompare(bId);
    });

    const N = nodes.length;
    currentY += LAYER_GAP;

    const cols = Math.min(6, N);
    const numRows = Math.ceil(N / cols);
    const hSpacing = Math.min(240, Math.max(MIN_H_SPACING, usableW / (cols + 1)));
    const vSpacing = 95;

    nodes.forEach((id, i) => {
      const row = Math.floor(i / cols);
      const col = i % cols;
      const nodesInThisRow = Math.min(cols, N - row * cols);
      const rowWidth = (nodesInThisRow - 1) * hSpacing;
      const x = -rowWidth / 2 + col * hSpacing;
      const y = currentY + row * vSpacing;
      positions[id] = { x, y };
    });

    currentY += (numRows - 1) * vSpacing;
  });

  const bbox = computeBBox(positions, elements);
  return { positions, bbox, targetId, elements, realElements: elements };
}

function fitCamera(cy, container, layoutInfo) {
  if (!cy || cy.destroyed() || !container || !layoutInfo) return;

  const W = Math.max(container.clientWidth || 0, 320);
  const H = Math.max(container.clientHeight || 0, 320);
  const bbox = layoutInfo.bbox || { x: 0, y: 0, w: 0, h: 0 };

  const requiredW = Math.max(bbox.w + 2 * PADDING, 250);
  const requiredH = Math.max(bbox.h + 2 * PADDING, 250);
  const zoom = Math.max(MIN_ZOOM, Math.min(MAX_ZOOM, Math.min(W / requiredW, H / requiredH)));

  cy.zoom(zoom);
  const centerX = bbox.x + bbox.w / 2;
  const centerY = bbox.y + bbox.h / 2;
  cy.pan({
    x: W / 2 - centerX * zoom,
    y: H / 2 - centerY * zoom,
  });
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
      hop_distance: 1,
      risk: { score: 0, risk_level: 'Low' },
    };
  };

  const addedNodeIds = new Set();
  const ensureNode = (addr, explicitInfo = null) => {
    const lower = (addr || '').toLowerCase();
    if (!lower) return null;
    if (addedNodeIds.has(lower)) return lower;
    addedNodeIds.add(lower);

    const info = explicitInfo || getNodeInfo(addr);
    const isTarget = lower === targetLower;
    const entityType = info.entity_type || 'Unknown';
    const hop = isTarget ? 0 : (info.hop_distance ?? 1);
    const riskLevel = info.risk?.risk_level || 'Low';
    const isUnknown = !info.entity || info.entity === 'Unknown';

    let displayLabel = '';
    if (isTarget) {
      displayLabel = `[ TARGET WALLET ]\n${shortenAddress(addr, 6, 4)}`;
    } else if (isUnknown) {
      displayLabel = shortenAddress(addr, 6, 4);
    } else {
      const cleanEntity = (info.entity || 'Entity').replace(/_/g, ' ');
      displayLabel = `${cleanEntity}\n${shortenAddress(addr, 6, 4)}`;
    }

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

  // Add all discovered nodes first
  discoveredList.forEach((info) => {
    if (info?.address) ensureNode(info.address, info);
  });
  if (targetLower) ensureNode(traceData.target_address);

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
            color: '#f1f5f9',
            'font-size': '10px',
            'font-family': 'monospace',
            'font-weight': 600,
            'text-valign': 'bottom',
            'text-halign': 'center',
            'text-margin-y': 8,
            'text-wrap': 'wrap',
            'text-max-width': '140px',
            'line-height': 1.3,
            'text-background-opacity': 0.92,
            'text-background-color': '#070b14',
            'text-background-padding': '4px',
            'text-background-shape': 'roundrectangle',
            'text-border-width': 1,
            'text-border-color': '#1e293b',
            'text-border-opacity': 0.9,
            'background-color': '#1e293b',
            'border-width': 2,
            'border-color': '#334155',
            width: OTHER_NODE_SIZE,
            height: OTHER_NODE_SIZE,
            'transition-property': 'background-color, border-color, opacity, width, height, shadow-blur',
            'transition-duration': '0.2s',
            'z-index': 10,
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
            'background-color': '#090d16',
            'border-width': 2,
            'border-color': '#64748b',
            'border-style': 'dashed',
            color: '#94a3b8',
          },
        },
        {
          selector: 'node.risk-critical',
          style: {
            'border-color': '#ef4444',
            'border-width': 3.5,
            'shadow-blur': 16,
            'shadow-color': '#ef4444',
            'shadow-opacity': 0.65,
          },
        },
        {
          selector: 'node.risk-high',
          style: {
            'border-color': '#f43f5e',
            'border-width': 3,
            'shadow-blur': 10,
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
          selector: 'node.risk-low',
          style: {
            'border-color': '#10b981',
            'border-width': 2,
          },
        },
        {
          selector: 'node.isTarget',
          style: {
            'background-color': '#00f0ff',
            'border-color': '#ffffff',
            'border-width': 4.5,
            width: TARGET_NODE_SIZE,
            height: TARGET_NODE_SIZE,
            'font-size': '11px',
            'font-weight': 'bold',
            color: '#00f0ff',
            'text-valign': 'top',
            'text-halign': 'center',
            'text-margin-y': -14,
            'text-border-color': '#00f0ff',
            'shadow-blur': 28,
            'shadow-color': '#00f0ff',
            'shadow-opacity': 0.9,
            'z-index': 999,
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
          selector: 'node.highlighted, node:selected',
          style: {
            'border-width': 4,
            'border-color': '#00f0ff',
            'shadow-blur': 20,
            'shadow-color': '#00f0ff',
            'shadow-opacity': 0.9,
            'z-index': 80,
          },
        },
        {
          selector: 'edge',
          style: {
            width: 1.8,
            'line-color': '#334155',
            'target-arrow-color': '#64748b',
            'target-arrow-shape': 'triangle',
            'curve-style': 'bezier',
            label: '',
            'font-size': '10px',
            'font-family': 'monospace',
            color: '#e2e8f0',
            'text-background-opacity': 0.92,
            'text-background-color': '#070b14',
            'text-background-padding': '3px',
            'text-background-shape': 'roundrectangle',
            'text-border-width': 1,
            'text-border-color': '#1e293b',
            opacity: 0.65,
            'arrow-scale': 0.95,
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
          selector: 'edge.edge-hot, edge.edge-hover',
          style: {
            label: 'data(label)',
            'line-color': '#00f0ff',
            'target-arrow-color': '#00f0ff',
            width: 2.8,
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

  const [showSearch, setShowSearch] = useState(false);
  const [showLegend, setShowLegend] = useState(false);
  const [nodeSearchInput, setNodeSearchInput] = useState('');

  const discoveredNodes = traceData?.trace_results?.discovered_addresses || [];
  const matchingSearchNodes = discoveredNodes.filter((n) => {
    if (!nodeSearchInput.trim()) return false;
    const q = nodeSearchInput.toLowerCase();
    return (
      (n.address || '').toLowerCase().includes(q) ||
      (n.entity || '').toLowerCase().includes(q) ||
      (n.entity_type || '').toLowerCase().includes(q)
    );
  });

  const handleJumpToNode = (addr) => {
    if (!cyRef.current || cyRef.current.destroyed()) return;
    const node = cyRef.current.getElementById((addr || '').toLowerCase());
    if (node && node.length) {
      cyRef.current.elements().unselect();
      node.select();
      selectedNodeIdRef.current = node.id();
      applyHighlight(cyRef.current, node.id());
      if (onSelectNode) {
        onSelectNode(node.data('info') || { address: addr });
      }
      cyRef.current.animate({
        center: { eles: node },
        zoom: 1.3,
        duration: 450
      });
      setShowSearch(false);
      setNodeSearchInput('');
    }
  };

  return (
    <div className="relative w-full h-full min-h-[580px] lg:min-h-[640px] cyber-panel rounded-xl overflow-hidden border border-slate-800/80">
      <div ref={containerRef} className="cytoscape-container w-full h-full" />

      {/* Floating Toolbar */}
      <GraphToolbar
        onZoomIn={handleZoomIn}
        onZoomOut={handleZoomOut}
        onFitTarget={handleFitTarget}
        onResetLayout={handleResetLayout}
        showEdgeLabels={showEdgeLabels}
        setShowEdgeLabels={setShowEdgeLabels}
        onToggleSearch={() => setShowSearch(!showSearch)}
        showSearch={showSearch}
        onToggleLegend={() => setShowLegend(!showLegend)}
        showLegend={showLegend}
      />

      {/* Inline Node Search Dropdown */}
      {showSearch && (
        <div className="absolute top-4 left-4 z-30 cyber-panel p-3 rounded-xl border border-slate-700/90 shadow-2xl backdrop-blur-md w-72 space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-[10px] font-mono uppercase tracking-wider text-cyan-400 font-bold">
              Find Wallet in Graph
            </span>
            <button
              onClick={() => setShowSearch(false)}
              className="text-slate-400 hover:text-white text-xs px-1"
            >
              ✕
            </button>
          </div>
          <input
            type="text"
            value={nodeSearchInput}
            onChange={(e) => setNodeSearchInput(e.target.value)}
            placeholder="Type address, entity (e.g. Tornado)..."
            className="w-full px-2.5 py-1.5 bg-slate-950/90 border border-slate-700/80 rounded-lg text-xs text-white placeholder-slate-500 font-mono focus:outline-none focus:border-cyan-400"
            autoFocus
          />
          {nodeSearchInput.trim() && (
            <div className="max-h-48 overflow-y-auto space-y-1 pt-1">
              {matchingSearchNodes.slice(0, 5).map((n) => (
                <button
                  key={n.address}
                  onClick={() => handleJumpToNode(n.address)}
                  className="w-full text-left p-1.5 rounded-lg hover:bg-slate-800/90 flex flex-col font-mono text-xs transition border border-transparent hover:border-slate-700"
                >
                  <span className="text-white font-semibold truncate">
                    {n.entity && n.entity !== 'Unknown' ? n.entity : shortenAddress(n.address, 8, 6)}
                  </span>
                  <span className="text-[10px] text-slate-400 truncate">
                    {shortenAddress(n.address, 10, 8)} &bull; Hop {n.hop_distance ?? 0}
                  </span>
                </button>
              ))}
              {matchingSearchNodes.length === 0 && (
                <div className="text-[11px] text-slate-500 py-2 text-center font-mono">
                  No matching nodes found
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* Forensic Classification Legend */}
      {showLegend && (
        <div className="absolute bottom-12 right-4 z-30 cyber-panel p-3.5 rounded-xl border border-slate-700/90 shadow-2xl backdrop-blur-md w-64 space-y-2.5 text-xs font-mono">
          <div className="flex items-center justify-between border-b border-slate-800 pb-2">
            <span className="text-[10px] uppercase font-bold text-cyan-400 tracking-wider">
              Forensic Legend
            </span>
            <button
              onClick={() => setShowLegend(false)}
              className="text-slate-400 hover:text-white text-xs px-1"
            >
              ✕
            </button>
          </div>
          <div className="space-y-1.5 text-[11px]">
            <div className="flex items-center gap-2">
              <span className="w-3.5 h-3.5 rounded-full bg-cyan-400 border border-white shadow-[0_0_8px_#00f0ff]" />
              <span className="text-white font-bold">Target Wallet (Origin)</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="w-3.5 h-3.5 rounded-full bg-emerald-500 border border-emerald-300" />
              <span className="text-slate-300">VASP / Exchange</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="w-3.5 h-3.5 rounded-full bg-red-600 border border-red-400 shadow-[0_0_6px_#ef4444]" />
              <span className="text-slate-300">Privacy Mixer</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="w-3.5 h-3.5 rounded-full bg-purple-500 border border-purple-300" />
              <span className="text-slate-300">Cross-Chain Bridge</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="w-3.5 h-3.5 rounded-full bg-rose-500 border border-rose-300" />
              <span className="text-slate-300">Scam / Phishing Drainer</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="w-3.5 h-3.5 rounded-full bg-slate-900 border border-dashed border-slate-500" />
              <span className="text-slate-400">Unattributed Wallet</span>
            </div>
            <div className="pt-1 border-t border-slate-800 text-[10px] text-slate-400">
              <span className="text-red-400 font-bold">Red halo</span>: Critical threat &bull; <span className="text-rose-400 font-bold">Rose halo</span>: High risk
            </div>
          </div>
        </div>
      )}

      {/* Bottom Status / Navigation Guide */}
      <div className="absolute bottom-3 left-3 z-10 cyber-panel-subtle px-3 py-1.5 rounded-lg border border-slate-800/80 flex items-center gap-3 text-[10px] font-mono text-slate-400 pointer-events-none">
        <span className="flex items-center gap-1.5 text-cyan-300 font-semibold">
          <span className="w-2 h-2 rounded-full bg-cyan-400 animate-pulse" />
          Layered BFS Forensics
        </span>
        <span className="hidden sm:inline text-slate-600">&bull;</span>
        <span className="hidden sm:inline">Hop 0 (Top) &rarr; Hop N (Bottom)</span>
        <span className="hidden sm:inline text-slate-600">&bull;</span>
        <span className="hidden md:inline">Click node to inspect intelligence</span>
      </div>
    </div>
  );
}
