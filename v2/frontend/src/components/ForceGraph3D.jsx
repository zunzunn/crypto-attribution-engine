import React, { useEffect, useRef } from 'react';
import ForceGraph3D from '3d-force-graph';
import * as THREE from 'three';
import { ZoomIn, ZoomOut, Maximize2, RefreshCw, Eye } from 'lucide-react';
import { shortenAddress } from '../utils/formatters';

export default function ForceGraph3DComponent({ traceData, selectedNode, onSelectNode }) {
  const containerRef = useRef(null);
  const graphRef = useRef(null);

  useEffect(() => {
    if (!containerRef.current || !traceData || !traceData.graph) return;

    // Transform graph data into 3d-force-graph format
    const nodes = [];
    const links = [];

    const discoveredList = traceData.trace_results?.discovered_addresses || [];
    const nodeMap = new Map();
    discoveredList.forEach(n => nodeMap.set(n.address.toLowerCase(), n));

    const addedNodeIds = new Set();
    const addNode = (addr) => {
      const lower = addr.toLowerCase();
      if (addedNodeIds.has(lower)) return;
      addedNodeIds.add(lower);

      const info = nodeMap.get(lower) || {
        address: addr,
        entity: 'Unknown',
        entity_type: 'Unknown',
        hop_distance: 0,
        risk: { score: 0, risk_level: 'Low' }
      };

      const isTarget = lower === (traceData.target_address || '').toLowerCase();

      nodes.push({
        id: lower,
        address: addr,
        entity: info.entity,
        entityType: info.entity_type || 'Unknown',
        hopDistance: info.hop_distance ?? 0,
        riskScore: info.risk?.score ?? 0,
        riskLevel: info.risk?.risk_level ?? 'Low',
        isTarget: isTarget,
        info: info
      });
    };

    Object.entries(traceData.graph).forEach(([sourceAddr, txList]) => {
      addNode(sourceAddr);
      txList.forEach(tx => {
        if (!tx.to) return;
        addNode(tx.to);
        links.push({
          source: sourceAddr.toLowerCase(),
          target: tx.to.toLowerCase(),
          amount: tx.amount,
          asset: tx.symbol || tx.asset_type || 'ETH',
          hash: tx.hash
        });
      });
    });

    const gData = { nodes, links };

    // Clear previous canvas if any
    containerRef.current.innerHTML = '';

    // Initialize 3D Force Graph
    const Graph = ForceGraph3D()(containerRef.current)
      .graphData(gData)
      .backgroundColor('#0a0e17')
      .nodeId('id')
      .nodeLabel(node => `
        <div style="background: rgba(15,23,42,0.9); border: 1px solid #334155; padding: 6px 10px; border-radius: 6px; font-family: monospace; font-size: 11px; color: #fff; box-shadow: 0 4px 12px rgba(0,0,0,0.5);">
          <strong style="color: #38bdf8;">${node.entity !== 'Unknown' ? node.entity : shortenAddress(node.address)}</strong><br/>
          <span style="color: #94a3b8;">Type: ${node.entityType} | Risk: ${node.riskLevel} (${node.riskScore.toFixed(1)})</span>
        </div>
      `)
      .nodeThreeObject(node => {
        // Create custom emissive 3D Sphere geometry
        const radius = node.isTarget ? 7 : 5;
        const geometry = new THREE.SphereGeometry(radius, 32, 32);

        let color = '#64748b';
        let emissive = '#1e293b';
        const type = node.entityType.toUpperCase();

        if (type.includes('MIXER')) {
          color = '#ef4444';
          emissive = '#7f1d1d';
        } else if (type.includes('VASP') || type.includes('EXCHANGE')) {
          color = '#3b82f6';
          emissive = '#1e3a8a';
        } else if (type.includes('BRIDGE')) {
          color = '#f59e0b';
          emissive = '#78350f';
        } else if (type.includes('SCAM') || type.includes('FRAUD')) {
          color = '#a855f7';
          emissive = '#581c87';
        }

        if (node.isTarget) {
          color = '#00f0ff';
          emissive = '#0891b2';
        }

        const material = new THREE.MeshPhongMaterial({
          color: color,
          emissive: emissive,
          emissiveIntensity: 0.6,
          shininess: 80,
          transparent: true,
          opacity: 0.95
        });

        const mesh = new THREE.Mesh(geometry, material);

        // Add cyan ring for target node
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
      .linkColor(() => 'rgba(100, 116, 139, 0.4)')
      .linkWidth(1.5)
      .onNodeClick(node => {
        // Camera smooth Fly-To focus animation
        const distance = 80;
        const distRatio = 1 + distance / Math.hypot(node.x, node.y, node.z);

        Graph.cameraPosition(
          { x: node.x * distRatio, y: node.y * distRatio, z: node.z * distRatio },
          node,
          1500
        );

        if (onSelectNode) {
          onSelectNode(node.info || { address: node.address });
        }
      });

    // Add 3D Scene Lighting
    const scene = Graph.scene();
    const ambientLight = new THREE.AmbientLight(0xffffff, 1.2);
    const dirLight = new THREE.DirectionalLight(0x00f0ff, 1.5);
    dirLight.position.set(100, 100, 100);
    scene.add(ambientLight);
    scene.add(dirLight);

    graphRef.current = Graph;

    return () => {
      if (containerRef.current) {
        containerRef.current.innerHTML = '';
      }
    };
  }, [traceData]);

  const handleResetCamera = () => {
    if (graphRef.current) {
      graphRef.current.zoomToFit(1000, 60);
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
          <span>Controls: Left-drag to rotate | Right-drag to pan | Scroll to zoom | Click 3D node to focus</span>
        </div>
      </div>
    </div>
  );
}
