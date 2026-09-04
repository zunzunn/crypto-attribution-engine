import React, { useState, useEffect } from 'react';
import { Search, Play, RefreshCw, Zap, Layers, GitBranch, Box, LayoutGrid } from 'lucide-react';
import CytoscapeGraph from './CytoscapeGraph';
import ForceGraph3DComponent from './ForceGraph3D';
import AddressDrawer from './AddressDrawer';
import { fetchAddressTrace } from '../services/api';
import { shortenAddress } from '../utils/formatters';

export default function TraceView({ targetAddress: initialAddress, onAddressChange, onTraceComplete }) {
  const [targetAddress, setTargetAddress] = useState(initialAddress || '0x71C7656EC7ab88b098defB751B7401B5f6d8976F');
  const [maxHops, setMaxHops] = useState(3);
  const [useEtherscan, setUseEtherscan] = useState(false);
  const [viewMode, setViewMode] = useState('3D'); // '3D' or '2D'
  const [loading, setLoading] = useState(false);
  const [traceData, setTraceData] = useState(null);
  const [selectedNode, setSelectedNode] = useState(null);
  const [errorMsg, setErrorMsg] = useState('');

  useEffect(() => {
    if (initialAddress) {
      setTargetAddress(initialAddress);
      executeTrace(initialAddress, maxHops, useEtherscan);
    } else {
      executeTrace(targetAddress, maxHops, useEtherscan);
    }
  }, [initialAddress]);

  const executeTrace = async (addr, hops, etherscanFlag) => {
    if (!addr) return;
    setLoading(true);
    setErrorMsg('');
    try {
      const res = await fetchAddressTrace(addr, hops, etherscanFlag);
      if (res.data) {
        setTraceData(res.data);
        const discovered = res.data.trace_results?.discovered_addresses || [];
        const targetNode = discovered.find(n => n.address.toLowerCase() === addr.toLowerCase()) || discovered[0];
        setSelectedNode(targetNode || null);
        if (typeof onTraceComplete === 'function') {
          onTraceComplete(res.data, Boolean(res.isLive));
        }
      }
    } catch (err) {
      setErrorMsg(`Failed to execute trace: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleRunTrace = (e) => {
    e.preventDefault();
    if (onAddressChange) onAddressChange(targetAddress);
    executeTrace(targetAddress, maxHops, useEtherscan);
  };

  const patterns = traceData?.patterns || {};
  const patternSummary = patterns.summary || {};

  return (
    <div className="space-y-4">
      
      {/* Control Bar Panel */}
      <form onSubmit={handleRunTrace} className="glass-panel p-4 rounded-xl border border-slate-800 flex flex-col md:flex-row items-center justify-between gap-4">
        
        {/* Target Address Input */}
        <div className="flex-1 w-full relative">
          <label className="text-[10px] uppercase font-bold text-slate-400 block mb-1">Target Ethereum Wallet</label>
          <div className="relative">
            <input
              type="text"
              value={targetAddress}
              onChange={(e) => setTargetAddress(e.target.value)}
              placeholder="Enter suspect Ethereum address 0x..."
              className="w-full pl-9 pr-4 py-2 text-xs font-mono rounded-lg bg-slate-950 border border-slate-700/80 text-white placeholder-slate-500 focus:outline-none focus:border-cyan-500"
            />
            <Search className="w-4 h-4 text-slate-500 absolute left-3 top-2.5" />
          </div>
        </div>

        {/* Max Hops Slider */}
        <div className="w-full md:w-40">
          <div className="flex justify-between items-center text-[10px] uppercase font-bold text-slate-400 mb-1">
            <span>Trace Depth:</span>
            <span className="text-cyan-400 font-mono">{maxHops} Hops</span>
          </div>
          <input
            type="range"
            min="1"
            max="5"
            value={maxHops}
            onChange={(e) => setMaxHops(parseInt(e.target.value))}
            className="w-full h-1.5 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-cyan-400"
          />
        </div>

        {/* 2D / 3D Mode Toggle Switch */}
        <div className="flex items-center gap-1 bg-slate-950 p-1 rounded-lg border border-slate-800">
          <button
            type="button"
            onClick={() => setViewMode('3D')}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded text-xs font-bold transition ${
              viewMode === '3D'
                ? 'bg-gradient-to-r from-cyan-500 to-blue-600 text-white shadow-md shadow-cyan-950/50'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <Box className="w-3.5 h-3.5" />
            3D WebGL
          </button>
          <button
            type="button"
            onClick={() => setViewMode('2D')}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded text-xs font-bold transition ${
              viewMode === '2D'
                ? 'bg-gradient-to-r from-cyan-500 to-blue-600 text-white shadow-md shadow-cyan-950/50'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <LayoutGrid className="w-3.5 h-3.5" />
            2D Dagre
          </button>
        </div>

        {/* Action Button */}
        <div className="flex items-center gap-2 w-full md:w-auto self-end">
          <button
            type="submit"
            disabled={loading}
            className="w-full md:w-auto px-5 py-2 rounded-lg bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-white font-bold text-xs shadow-lg shadow-cyan-950/50 flex items-center justify-center gap-2 transition disabled:opacity-50"
          >
            {loading ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4 fill-white" />}
            {loading ? 'Tracing Graph...' : 'Run Forensic Trace'}
          </button>
        </div>

      </form>

      {/* Pattern Indicator Header Badges */}
      {traceData && (
        <div className="glass-panel p-3 rounded-xl border border-slate-800 flex flex-wrap items-center justify-between gap-3 text-xs">
          
          <div className="flex items-center gap-2">
            <span className="font-semibold text-slate-400">Target:</span>
            <span className="font-mono text-cyan-300 bg-cyan-950/60 px-2 py-0.5 rounded border border-cyan-800/50">
              {shortenAddress(traceData.target_address, 8, 6)}
            </span>
          </div>

          {/* Obfuscation Badges */}
          <div className="flex flex-wrap items-center gap-2">
            {patternSummary.has_fan_out && (
              <span className="px-2.5 py-1 rounded-full text-[11px] font-bold bg-amber-500/20 text-amber-300 border border-amber-500/40 flex items-center gap-1">
                <GitBranch className="w-3.5 h-3.5" /> Splitting (Fan-Out)
              </span>
            )}
            {patternSummary.has_fan_in && (
              <span className="px-2.5 py-1 rounded-full text-[11px] font-bold bg-amber-500/20 text-amber-300 border border-amber-500/40 flex items-center gap-1">
                <GitBranch className="w-3.5 h-3.5 rotate-180" /> Consolidation (Fan-In)
              </span>
            )}
            {patternSummary.has_rapid_hopping && (
              <span className="px-2.5 py-1 rounded-full text-[11px] font-bold bg-red-500/20 text-red-300 border border-red-500/40 flex items-center gap-1">
                <Zap className="w-3.5 h-3.5" /> Rapid Wallet Hopping
              </span>
            )}
            {patternSummary.has_layering && (
              <span className="px-2.5 py-1 rounded-full text-[11px] font-bold bg-purple-500/20 text-purple-300 border border-purple-500/40 flex items-center gap-1">
                <Layers className="w-3.5 h-3.5" /> Multi-hop Layering
              </span>
            )}
            {!patternSummary.total_patterns_detected && (
              <span className="text-slate-500 italic text-[11px]">No obfuscation anomalies detected</span>
            )}
          </div>

          <div className="text-slate-400 font-mono text-[11px]">
            {traceData.trace_results?.discovered_addresses?.length || 0} Nodes Traced
          </div>

        </div>
      )}

      {/* Main Workspace Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 h-[620px]">
        
        {/* Canvas (Spans 2 columns) */}
        <div className="lg:col-span-2 h-full">
          {viewMode === '3D' ? (
            <ForceGraph3DComponent
              traceData={traceData}
              selectedNode={selectedNode}
              onSelectNode={(nodeInfo) => setSelectedNode(nodeInfo)}
            />
          ) : (
            <CytoscapeGraph
              traceData={traceData}
              selectedNode={selectedNode}
              onSelectNode={(nodeInfo) => setSelectedNode(nodeInfo)}
            />
          )}
        </div>

        {/* Address Intelligence Drawer (Spans 1 column) */}
        <div className="h-full">
          <AddressDrawer
            selectedNode={selectedNode}
            onClose={() => setSelectedNode(null)}
          />
        </div>

      </div>

    </div>
  );
}
