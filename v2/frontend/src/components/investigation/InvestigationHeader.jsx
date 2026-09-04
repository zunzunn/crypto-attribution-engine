import React, { useState } from 'react';
import {
  ExternalLink,
  Copy,
  Check,
  RotateCcw,
  FileText,
  Filter,
  Box,
  LayoutGrid
} from 'lucide-react';
import { shortenAddress } from '../../utils/formatters';
import RiskBadge from '../common/RiskBadge';

export default function InvestigationHeader({
  targetAddress,
  caseId,
  overallRisk,
  isLive,
  liveStats,
  _maxHops,
  viewMode,
  setViewMode,
  showFilters,
  setShowFilters,
  onReTrace,
  onExportReport
}) {
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    if (targetAddress) {
      navigator.clipboard.writeText(targetAddress);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const riskScore = overallRisk?.score ?? 0;
  const riskLevel = overallRisk?.risk_level ?? 'Low';

  return (
    <div className="cyber-panel p-4 rounded-xl border border-slate-800/80 flex flex-col lg:flex-row items-start lg:items-center justify-between gap-4">
      {/* Target & Case Meta */}
      <div className="flex flex-wrap items-center gap-3">
        <div>
          <div className="flex items-center gap-2">
            <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-900 border border-slate-800 text-cyan-400 font-bold">
              {caseId || 'CASE-2026'}
            </span>
            <span className="text-[10px] uppercase font-mono tracking-wider text-slate-400">Target Address</span>
          </div>

          <div className="flex items-center gap-2 mt-1">
            <span className="text-sm sm:text-base font-bold font-mono text-white tracking-wide" title={targetAddress}>
              {shortenAddress(targetAddress, 10, 8)}
            </span>
            <button
              onClick={handleCopy}
              className="p-1 rounded hover:bg-slate-800 text-slate-400 hover:text-cyan-300 transition"
              title="Copy Target Address"
            >
              {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
            </button>
            <a
              href={`https://etherscan.io/address/${targetAddress}`}
              target="_blank"
              rel="noreferrer"
              className="p-1 rounded hover:bg-slate-800 text-slate-400 hover:text-cyan-300 transition"
              title="View on Etherscan"
            >
              <ExternalLink className="w-3.5 h-3.5" />
            </a>
          </div>
        </div>

        {/* Risk Badge Pill */}
        <div className="pl-3 border-l border-slate-800">
          <span className="text-[10px] uppercase font-mono tracking-wider text-slate-400 block mb-1">Risk Score</span>
          <RiskBadge level={riskLevel} score={riskScore} size="sm" />
        </div>

        {/* Live Data Badge */}
        <div className="pl-3 border-l border-slate-800 hidden sm:block">
          <span className="text-[10px] uppercase font-mono tracking-wider text-slate-400 block mb-1">Data Source</span>
          <div className="flex items-center gap-1.5 text-xs font-mono">
            <span className={`w-2 h-2 rounded-full ${isLive ? 'bg-cyan-400 animate-pulse' : 'bg-slate-500'}`} />
            <span className={isLive ? 'text-cyan-300 font-semibold' : 'text-slate-400'}>
              {isLive ? 'Mainnet Live' : 'Cached Local'}
            </span>
          </div>
        </div>

        {/* Live Stats Pill if available */}
        {liveStats && (
          <div className="pl-3 border-l border-slate-800 hidden xl:block text-[10px] font-mono text-slate-400">
            <div>Fetched: <span className="text-white font-bold">{liveStats.addresses_fetched}</span> addrs</div>
            <div>Txs: <span className="text-white font-bold">{liveStats.transactions_fetched}</span> &bull; Hops: <span className="text-cyan-400">{liveStats.hops_processed}</span></div>
          </div>
        )}
      </div>

      {/* Controls & Actions */}
      <div className="flex flex-wrap items-center gap-2 self-end lg:self-center w-full lg:w-auto justify-end">
        {/* Toggle Filters Panel */}
        <button
          onClick={() => setShowFilters(!showFilters)}
          className={`px-3 py-1.5 rounded-lg border text-xs font-medium flex items-center gap-1.5 transition ${
            showFilters
              ? 'bg-slate-800 text-cyan-300 border-slate-700'
              : 'bg-slate-900/90 text-slate-400 border-slate-800 hover:text-white'
          }`}
          title="Toggle Filters Panel"
        >
          <Filter className="w-3.5 h-3.5" />
          <span className="hidden sm:inline">Filters</span>
        </button>

        {/* 2D / 3D Mode Toggle Switch */}
        <div className="flex items-center bg-slate-950 p-0.5 rounded-lg border border-slate-800">
          <button
            type="button"
            onClick={() => setViewMode('2D')}
            className={`flex items-center gap-1.5 px-2.5 py-1 rounded text-xs font-semibold transition ${
              viewMode === '2D'
                ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/40 shadow-sm'
                : 'text-slate-400 hover:text-slate-200'
            }`}
            title="2D Layered Cytoscape Graph"
          >
            <LayoutGrid className="w-3.5 h-3.5" />
            2D Forensics
          </button>
          <button
            type="button"
            onClick={() => setViewMode('3D')}
            className={`flex items-center gap-1.5 px-2.5 py-1 rounded text-xs font-semibold transition ${
              viewMode === '3D'
                ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/40 shadow-sm'
                : 'text-slate-400 hover:text-slate-200'
            }`}
            title="3D WebGL Cyberspace Force Graph"
          >
            <Box className="w-3.5 h-3.5" />
            3D Force
          </button>
        </div>

        {/* Re-trace Button */}
        {onReTrace && (
          <button
            onClick={onReTrace}
            className="p-1.5 rounded-lg bg-slate-900 border border-slate-800 text-slate-400 hover:text-cyan-300 hover:bg-slate-850 transition"
            title="Re-run Forensic Trace"
          >
            <RotateCcw className="w-3.5 h-3.5" />
          </button>
        )}

        {/* Export Report CTA */}
        {onExportReport && (
          <button
            onClick={onExportReport}
            className="px-3.5 py-1.5 rounded-lg bg-cyan-500/15 hover:bg-cyan-500/25 border border-cyan-500/30 text-cyan-300 font-semibold text-xs flex items-center gap-1.5 transition shadow-sm"
          >
            <FileText className="w-3.5 h-3.5" />
            Report
          </button>
        )}
      </div>
    </div>
  );
}
