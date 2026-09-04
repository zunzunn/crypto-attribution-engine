import React from 'react';
import {
  Shield,
  Server,
  Cpu,
  Database,
  Layers,
  Zap
} from 'lucide-react';

export default function SystemAboutView({ apiLive, apiLatency, onCheckHealth }) {
  return (
    <div className="max-w-4xl mx-auto space-y-6 py-4">
      {/* Brand Header */}
      <div className="cyber-panel p-6 rounded-2xl border border-slate-800/80 bg-gradient-to-r from-slate-900/90 via-slate-900/70 to-cyan-950/30">
        <div className="flex items-center gap-3">
          <div className="w-12 h-12 rounded-2xl bg-cyan-500/15 border border-cyan-500/30 text-cyan-400 flex items-center justify-center shadow-lg shadow-cyan-950/50">
            <Shield className="w-7 h-7" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-xl font-bold text-white tracking-wide">
                Crypto Attribution Engine
              </h2>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-cyan-950 text-cyan-400 border border-cyan-800/60 font-bold">
                VERSION 2.0.0
              </span>
            </div>
            <p className="text-xs text-slate-400 mt-0.5">
              Autonomous On-Chain Forensic Graph Intelligence Platform
            </p>
          </div>
        </div>
      </div>

      {/* Backend & Connectivity Status Card */}
      <div className="cyber-panel p-6 rounded-2xl border border-slate-800/80 space-y-4">
        <div className="flex items-center justify-between border-b border-slate-800 pb-3">
          <div className="flex items-center gap-2">
            <Server className="w-4 h-4 text-cyan-400" />
            <h3 className="text-sm font-bold text-white uppercase tracking-wider">Engine Connectivity & Telemetry</h3>
          </div>
          <button
            onClick={onCheckHealth}
            className="px-3 py-1 rounded-lg bg-slate-900 hover:bg-slate-800 border border-slate-700 text-xs text-cyan-300 font-mono transition"
          >
            Check Ping
          </button>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 font-mono text-xs">
          <div className="p-3 rounded-xl bg-slate-950/80 border border-slate-800">
            <span className="text-[10px] text-slate-500 uppercase block">FastAPI Server</span>
            <div className="flex items-center gap-2 mt-1">
              <span className={`w-2 h-2 rounded-full ${apiLive ? 'bg-emerald-400 animate-pulse' : 'bg-amber-400'}`} />
              <span className="font-bold text-white">{apiLive ? 'ONLINE (Port 8000)' : 'FALLBACK MOCK'}</span>
            </div>
          </div>

          <div className="p-3 rounded-xl bg-slate-950/80 border border-slate-800">
            <span className="text-[10px] text-slate-500 uppercase block">Ping Latency</span>
            <span className="font-bold text-cyan-300 mt-1 block">
              {apiLatency !== null ? `${apiLatency} ms` : 'N/A'}
            </span>
          </div>

          <div className="p-3 rounded-xl bg-slate-950/80 border border-slate-800">
            <span className="text-[10px] text-slate-500 uppercase block">Target Network</span>
            <span className="font-bold text-white mt-1 block">Ethereum Mainnet (ID: 1)</span>
          </div>
        </div>
      </div>

      {/* Forensic Engine Architecture */}
      <div className="cyber-panel p-6 rounded-2xl border border-slate-800/80 space-y-4">
        <div className="flex items-center gap-2 border-b border-slate-800 pb-3">
          <Cpu className="w-4 h-4 text-cyan-400" />
          <h3 className="text-sm font-bold text-white uppercase tracking-wider">Forensic Methodology & Algorithm Specs</h3>
        </div>

        <div className="space-y-3 text-xs text-slate-300 leading-relaxed">
          <div className="p-3.5 rounded-xl bg-slate-950/60 border border-slate-800 space-y-1">
            <h4 className="font-bold text-white flex items-center gap-2">
              <Layers className="w-4 h-4 text-cyan-400" />
              1. Multi-Hop BFS Graph Traversal
            </h4>
            <p className="text-slate-400 text-[11px]">
              Traverses directed Ethereum transaction graphs using bounded breadth-first search. Automatically aggregates multiple transfers between identical counterparties into unified volume conduits to prevent graph clutter.
            </p>
          </div>

          <div className="p-3.5 rounded-xl bg-slate-950/60 border border-slate-800 space-y-1">
            <h4 className="font-bold text-white flex items-center gap-2">
              <Database className="w-4 h-4 text-blue-400" />
              2. Probabilistic Entity Attribution Registry
            </h4>
            <p className="text-slate-400 text-[11px]">
              Cross-references discovered wallet and contract addresses against centralized exchanges (VASPs), OFAC sanctioned mixers, canonical cross-chain bridges, and fraud drainers with confidence provenance scoring.
            </p>
          </div>

          <div className="p-3.5 rounded-xl bg-slate-950/60 border border-slate-800 space-y-1">
            <h4 className="font-bold text-white flex items-center gap-2">
              <Zap className="w-4 h-4 text-amber-400" />
              3. Behavioral Obfuscation Heuristics
            </h4>
            <p className="text-slate-400 text-[11px]">
              Autonomous detectors flag money-laundering tactics: <code>FAN_OUT_SPLITTING</code> (smurfing), <code>FAN_IN_CONSOLIDATION</code>, <code>RAPID_WALLET_HOPPING</code> (rapid pass-through under 15 minutes), and <code>MULTI_HOP_LAYERING</code>.
            </p>
          </div>
        </div>
      </div>

      {/* Integration & Standards */}
      <div className="cyber-panel p-5 rounded-xl border border-slate-800/80 flex flex-col sm:flex-row items-center justify-between gap-4 text-xs text-slate-400 font-mono">
        <div>
          <span>Integrated with SIH Cyber Crime Reporting Standards</span>
          <p className="text-[10px] text-slate-500 mt-0.5">Court-admissible forensic evidence dossier format</p>
        </div>
        <span className="text-cyan-400 font-bold">LAW ENFORCEMENT GRADE</span>
      </div>
    </div>
  );
}
