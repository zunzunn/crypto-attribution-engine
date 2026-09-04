import React, { useEffect, useRef, useState } from 'react';
import ForceGraph3D from '3d-force-graph';
import * as THREE from 'three';
import { RefreshCw, AlertTriangle } from 'lucide-react';
import { shortenAddress } from '../utils/formatters';

const ENTITY_COLORS = {
  MIXER: { color: '#ef4444', emissive: '#7f1d1d' },
  VASP: { color: '#3b82f6', emissive: '#1e3a8a' },
  BRIDGE: { color: '#f59e0b', emissive: '#78350f' },
  SCAM: { color: '#a855f7', emissive: '#581c87' },
};

function paletteFor(entityType) {
  const t = (entityType || 'Unknown').toUpperCase();
  if (t.includes('MIXER')) return ENTITY_COLORS.MIXER;
  if (t.includes('VASP') || t.includes('EXCHANGE')) return ENTITY_COLORS.VASP;
  if (t.includes('BRIDGE')) return ENTITY_COLORS.BRIDGE;
  if (t.includes('SCAM') || t.includes('FRAUD')) return ENTITY_COLORS.SCAM;
  return { color: '#64748b', emissive: '#1e293b' };
}

// Convert a backend `graph` object of the form
//   { "0xsender->0xreceiver": [transferObj, ...] }
// into the {nodes, links} shape that 3d-force-graph expects.
// Also aggregates all transfers between the same (source, target) pair into a
// single link so dense wallets render cleanly.
function buildGraphData(traceData) {
  const nodes = [];
  const links = [];
  const targetLower = (traceData.target_address || '').toLowerCase();

  const nodeMap = new Map();
  const discoveredList = traceData.trace_results?.discovered_addresses || [];
  discoveredList.forEach((n) => {
    if (n?.address) nodeMap.set(n.address.toLowerCase(), n);
  });

  const added = new Set();
  const addNode = (addr) => {
    if (!addr) return null;
    const lower = String(addr).toLowerCase();
    if (!lower || added.has(lower)) return lower;
    added.add(lower);

    const info = nodeMap.get(lower) || {
      address: addr,
      entity: 'Unknown',
      entity_type: 'Unknown',
      hop_distance: 0,
      risk: { score: 0, risk_level: 'Low' },
    };

    nodes.push({
      id: lower,
      address: addr,
      entity: info.entity,
      entityType: info.entity_type || 'Unknown',
      hopDistance: info.hop_distance ?? 0,
      riskScore: info.risk?.score || 0,
      riskLevel: info.risk?.risk_level || 'Low',
      isTarget: lower === targetLower,
      info,
    });
    return lower;
  };

  // Index graph edges. The backend stores them as a dict keyed by
  // "SRC->DST" (sender address on the left, receiver on the right) where
  // the value is the list of transfer objects. The transfer objects also
  // carry from_address / to_address so we read either source.
  const rawGraph = traceData.graph && typeof traceData.graph === 'object' ? traceData.graph : {};
  const edgeEntries = Object.entries(rawGraph);

  const linkAgg = new Map();

  edgeEntries.forEach(([edgeKey, txList]) => {
    // Try to derive the (source, target) from the key. If that fails (e.g.
    // the backend returns a graph where keys aren't "src->dst"), fall back
    // to reading the first transfer's from_address / to_address.
    let sourceAddr = null;
    let receiverFromKey = null;
    if (typeof edgeKey === 'string' && edgeKey.includes('->')) {
      const parts = edgeKey.split('->');
      if (parts.length === 2) {
        sourceAddr = parts[0];
        receiverFromKey = parts[1];
      }
    }

    const transfers = Array.isArray(txList) ? txList : [];

    transfers.forEach((tx) => {
      const txSource = (tx && (tx.from_address || tx.from)) || sourceAddr;
      const txTarget = (tx && (tx.to_address || tx.to)) || receiverFromKey;
      if (!txSource || !txTarget) return;
      const sourceId = addNode(txSource);
      const targetId = addNode(txTarget);
      if (!sourceId || !targetId || sourceId === targetId) return;

      const key = `${sourceId}->${targetId}`;
      let entry = linkAgg.get(key);
      if (!entry) {
        entry = {
          source: sourceId,
          target: targetId,
          totalAmount: 0,
          txCount: 0,
          representativeAmount: 0,
          representativeAsset: 'ETH',
        };
        linkAgg.set(key, entry);
      }
      const amt = parseFloat(tx.amount);
      if (Number.isFinite(amt) && amt > 0) {
        entry.totalAmount += amt;
        if (amt > entry.representativeAmount) {
          entry.representativeAmount = amt;
          entry.representativeAsset = tx.symbol || tx.asset_type || 'ETH';
        }
      }
      entry.txCount += 1;
    });
  });

  // Safety: drop any link that references a node id that we did not add.
  const ids = new Set(nodes.map((n) => n.id));
  linkAgg.forEach((entry) => {
    if (ids.has(entry.source) && ids.has(entry.target)) {
      links.push(entry);
    }
  });

  return { nodes, links };
}

// Position the camera so that the entire graph is visible inside the container.
// We compute the bounding box of every node position and place the camera
// outside that box along the +Z axis, then point the look-at target at the
// geometric centre — all in the SAME coordinate system that the meshes,
// sprites and link lines use.
function frameToContainer(Graph, container) {
  if (!Graph || !container) return;
  const width = Math.max(container.clientWidth || 0, 320);
  const height = Math.max(container.clientHeight || 0, 320);
  try { Graph.width(width); } catch (_) {}
  try { Graph.height(height); } catch (_) {}

  const data = Graph.graphData();
  const nodes = data.nodes || [];
  if (!nodes.length) return;

  let valid = 0;
  let minX = Infinity, minY = Infinity, minZ = Infinity;
  let maxX = -Infinity, maxY = -Infinity, maxZ = -Infinity;
  nodes.forEach((n) => {
    if (!Number.isFinite(n.x) || !Number.isFinite(n.y) || !Number.isFinite(n.z)) return;
    valid += 1;
    if (n.x < minX) minX = n.x;
    if (n.y < minY) minY = n.y;
    if (n.z < minZ) minZ = n.z;
    if (n.x > maxX) maxX = n.x;
    if (n.y > maxY) maxY = n.y;
    if (n.z > maxZ) maxZ = n.z;
  });
  if (!valid) return; // simulation not ready yet

  const cx = (minX + maxX) / 2;
  const cy = (minY + maxY) / 2;
  const cz = (minZ + maxZ) / 2;
  const dx = maxX - minX;
  const dy = maxY - minY;
  const dz = maxZ - minZ;
  const span = Math.max(dx, dy, dz, 1);

  // Camera distance derived from the larger of width / height so the graph
  // always fits in both dimensions.
  const aspect = width / height;
  const fov = (Graph.camera && Graph.camera.fov) ? (Graph.camera.fov * Math.PI / 180) : Math.PI / 4;
  const distH = (span / 2) / Math.tan(fov / 2);
  const distW = (span / 2) / Math.tan(fov / 2) / aspect;
  const distance = Math.max(distH, distW) * 1.7; // padding

  try {
    Graph.cameraPosition(
      { x: cx, y: cy, z: cz + distance },
      { x: cx, y: cy, z: cz },
      900,
    );
  } catch (_) { /* ignore */ }
}

export default function ForceGraph3DComponent({ traceData, selectedNode, onSelectNode }) {
  const containerRef = useRef(null);
  const graphRef = useRef(null);
  const resizeObserverRef = useRef(null);
  const [renderError, setRenderError] = useState(null);
  const [diag, setDiag] = useState(null);

  useEffect(() => {
    setRenderError(null);

    if (!containerRef.current) {
      setRenderError('Graph container is not mounted.');
      return;
    }
    if (!traceData) {
      setDiag(null);
      return;
    }
    if (!traceData.graph || typeof traceData.graph !== 'object') {
      setRenderError('Trace response has no graph data.');
      return;
    }

    const container = containerRef.current;
    const measuredW = Math.max(container.clientWidth || 0, 320);
    const measuredH = Math.max(container.clientHeight || 0, 320);

    // Clear any leftover canvas from a previous run.
    container.innerHTML = '';

    let Graph;
    try {
      const gData = buildGraphData(traceData);

      // Surface diagnostics for the operator so a blank graph is debuggable.
      const diagnostics = {
        nodeCount: gData.nodes.length,
        linkCount: gData.links.length,
        containerWidth: measuredW,
        containerHeight: measuredH,
        firstNode: gData.nodes[0] || null,
        firstLink: gData.links[0] || null,
      };
      setDiag(diagnostics);

      // eslint-disable-next-line no-console
      console.info('[ForceGraph3D] mounting graph', diagnostics);

      if (!gData.nodes.length) {
        setRenderError('No address nodes could be derived from the trace graph.');
        return;
      }

      Graph = ForceGraph3D()(container)
        .width(measuredW)
        .height(measuredH)
        .backgroundColor('#0a0e17')
        .nodeId('id')
        .nodeRelSize(6)
        .nodeLabel((node) => `
          <div style="background: rgba(15,23,42,0.9); border: 1px solid #334155; padding: 6px 10px; border-radius: 6px; font-family: monospace; font-size: 11px; color: #fff; box-shadow: 0 4px 12px rgba(0,0,0,0.5);">
            <strong style="color: #38bdf8;">${node.entity && node.entity !== 'Unknown' ? node.entity : shortenAddress(node.address)}</strong><br/>
            <span style="color: #94a3b8;">Type: ${node.entityType} | Risk: ${node.riskLevel} (${node.riskScore.toFixed(1)})</span>
          </div>
        `)
        .nodeThreeObject((node) => {
          const radius = node.isTarget ? 7 : 5;
          const geometry = new THREE.SphereGeometry(radius, 32, 32);

          let color = '#64748b';
          let emissive = '#1e293b';
          if (node.isTarget) {
            color = '#00f0ff';
            emissive = '#0891b2';
          } else {
            const palette = paletteFor(node.entityType);
            color = palette.color;
            emissive = palette.emissive;
          }

          const material = new THREE.MeshPhongMaterial({
            color,
            emissive,
            emissiveIntensity: 0.6,
            shininess: 80,
            transparent: true,
            opacity: 0.95,
          });

          const mesh = new THREE.Mesh(geometry, material);

          if (node.isTarget) {
            const ringGeo = new THREE.RingGeometry(8.5, 10, 32);
            const ringMat = new THREE.MeshBasicMaterial({ color: 0x00f0ff, side: THREE.DoubleSide });
            const ringMesh = new THREE.Mesh(ringGeo, ringMat);
            mesh.add(ringMesh);
          }

          return mesh;
        })
        .linkDirectionalParticles(2)
        .linkDirectionalParticleSpeed(0.008)
        .linkDirectionalParticleWidth(2.5)
        .linkDirectionalParticleColor(() => '#00f0ff')
        .linkColor(() => 'rgba(100, 116, 139, 0.5)')
        .linkWidth(1.5)
        .linkCurvature(0.05)
        .onNodeClick((node) => {
          const distance = 80;
          const distRatio = 1 + distance / Math.hypot(
            Number.isFinite(node.x) ? node.x : 1,
            Number.isFinite(node.y) ? node.y : 1,
            Number.isFinite(node.z) ? node.z : 1,
          );
          Graph.cameraPosition(
            { x: (node.x || 0) * distRatio, y: (node.y || 0) * distRatio, z: (node.z || 0) * distRatio },
            node,
            1200,
          );
          if (onSelectNode) onSelectNode(node.info || { address: node.address });
        });

      // Explicit data assignment — 3d-force-graph starts its simulation here.
      Graph.graphData(gData);

      // Lighting
      const scene = Graph.scene();
      scene.add(new THREE.AmbientLight(0xffffff, 1.2));
      const dirLight = new THREE.DirectionalLight(0x00f0ff, 1.5);
      dirLight.position.set(100, 100, 100);
      scene.add(dirLight);

      graphRef.current = Graph;
    } catch (err) {
      // eslint-disable-next-line no-console
      console.error('[ForceGraph3D] failed to initialise 3D graph:', err);
      setRenderError(`3D graph failed to initialise: ${err && err.message ? err.message : String(err)}`);
      return undefined;
    }

    // Camera framing: retry several times because positions update during the
    // first d3-force simulation ticks.
    let frameAttempts = 0;
    const frame = () => {
      frameAttempts += 1;
      if (graphRef.current && containerRef.current) {
        frameToContainer(graphRef.current, containerRef.current);
      }
      if (frameAttempts < 8) setTimeout(frame, 250);
    };
    setTimeout(frame, 150);
    setTimeout(frame, 1200);

    // Resize handling — read actual container dims.
    const handleResize = () => {
      if (!graphRef.current || !containerRef.current) return;
      const w = Math.max(containerRef.current.clientWidth || 0, 320);
      const h = Math.max(containerRef.current.clientHeight || 0, 320);
      try { graphRef.current.width(w); } catch (_) {}
      try { graphRef.current.height(h); } catch (_) {}
      setTimeout(() => {
        if (graphRef.current && containerRef.current) {
          frameToContainer(graphRef.current, containerRef.current);
        }
      }, 80);
    };
    window.addEventListener('resize', handleResize);
    if (typeof ResizeObserver !== 'undefined') {
      resizeObserverRef.current = new ResizeObserver(handleResize);
      resizeObserverRef.current.observe(container);
    }

    return () => {
      window.removeEventListener('resize', handleResize);
      if (resizeObserverRef.current) {
        resizeObserverRef.current.disconnect();
        resizeObserverRef.current = null;
      }
      if (Graph && typeof Graph.pauseAnimation === 'function') {
        try { Graph.pauseAnimation(); } catch (_) {}
      }
      container.innerHTML = '';
      graphRef.current = null;
    };
  }, [traceData]);

  const handleResetCamera = () => {
    if (graphRef.current && containerRef.current) {
      frameToContainer(graphRef.current, containerRef.current);
    }
  };

  return (
    <div className="relative w-full h-full min-h-[500px] glass-panel rounded-xl overflow-hidden border border-slate-800">
      {/* 3D Canvas Container */}
      <div ref={containerRef} className="w-full h-full absolute inset-0" />

      {/* Floating Controls Overlay */}
      <div className="absolute top-4 right-4 flex flex-col gap-2 z-10">
        <button
          onClick={handleResetCamera}
          title="Reset 3D Camera View"
          className="p-2 rounded-lg bg-slate-900/90 text-slate-300 hover:text-cyan-400 border border-slate-700/60 shadow-lg transition"
        >
          <RefreshCw className="w-4 h-4" />
        </button>
      </div>

      {/* 3D Legend & Controls Hint */}
      <div className="absolute bottom-4 left-4 z-10 glass-card p-3 rounded-lg border border-slate-800 flex flex-col gap-2 text-xs">
        <div className="flex items-center gap-3">
          <span className="font-bold text-cyan-400">3D Matrix Legend:</span>
          <div className="flex items-center gap-1.5"><span className="w-2.5 h-2.5 rounded-full bg-red-500 shadow-sm shadow-red-500/50"></span><span className="text-slate-300">Mixer</span></div>
          <div className="flex items-center gap-1.5"><span className="w-2.5 h-2.5 rounded-full bg-blue-500 shadow-sm shadow-blue-500/50"></span><span className="text-slate-300">VASP</span></div>
          <div className="flex items-center gap-1.5"><span className="w-2.5 h-2.5 rounded-full bg-amber-500 shadow-sm shadow-amber-500/50"></span><span className="text-slate-300">Bridge</span></div>
          <div className="flex items-center gap-1.5"><span className="w-2.5 h-2.5 rounded-full bg-purple-500 shadow-sm shadow-purple-500/50"></span><span className="text-slate-300">Scam</span></div>
        </div>
        <div className="text-[10px] text-slate-400 flex items-center gap-2">
          <span>Left-drag: rotate | Right-drag: pan | Scroll: zoom | Click: focus</span>
        </div>
        {diag && (
          <div className="text-[10px] text-slate-500 font-mono pt-1 border-t border-slate-700/60">
            nodes={diag.nodeCount} links={diag.linkCount} canvas={diag.containerWidth}×{diag.containerHeight}
          </div>
        )}
      </div>

      {renderError && (
        <div className="absolute inset-0 flex items-center justify-center bg-slate-950/85 z-20">
          <div className="glass-card p-4 rounded-lg border border-amber-500/40 text-xs text-amber-200 max-w-md">
            <div className="flex items-center gap-2 mb-2">
              <AlertTriangle className="w-4 h-4 text-amber-400" />
              <span className="font-bold">3D graph unavailable</span>
            </div>
            <p className="text-slate-300">{renderError}</p>
          </div>
        </div>
      )}
    </div>
  );
}