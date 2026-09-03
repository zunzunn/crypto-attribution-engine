import React from 'react';
import { Shield, AlertTriangle, ExternalLink, Copy, Check, Info, Zap, Layers, GitBranch, ArrowRightLeft } from 'lucide-react';
import { shortenAddress, getRiskBadgeStyle, getEntityBadgeStyle } from '../utils/formatters';

export default function AddressDrawer({ selectedNode, onClose }) {
  const [copied, setCopied] = React.useState(false);

  if (!selectedNode) {
    return (
      <div className="glass-panel rounded-xl p-6 border border-slate-800 flex flex-col items-center justify-center text-center h-full text-slate-500">
        <Info className="w-8 h-8 mb-2 opacity-50 text-cyan-400" />
        <p className="text-sm font-medium text-slate-300">No Address Selected</p>
        <p className="text-xs text-slate-500 mt-1">Click on any node in the transaction graph to inspect its attribution, evidence, and risk breakdown.</p>
      </div>
    );
  }

  const {
    address = '',
    entity = 'Unknown',
    entity_type = 'Unknown',
    confidence = 0,
    sources = [],
    hop_distance = 0,
    evidence = '',
    risk = { score: 0, risk_level: 'Low', reasons: [] }
  } = selectedNode;

  const handleCopy = () => {
    navigator.clipboard.writeText(address);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const confidencePct = Math.round((confidence || 0) * 100);

  return (
    <div className="glass-panel rounded-xl p-5 border border-slate-800 flex flex-col gap-4 overflow-y-auto max-h-full">
      
      {/* Header */}
      <div className="flex items-start justify-between border-b border-slate-800 pb-3">
        <div>
          <span className="text-[10px] font-bold tracking-wider text-cyan-400 uppercase">Address Intelligence</span>
          <h3 className="text-base font-bold text-white mt-0.5">{entity !== 'Unknown' ? entity : 'Unlabeled Address'}</h3>
        </div>
        <button
          onClick={onClose}
          className="text-slate-500 hover:text-slate-300 text-xs px-2 py-1 rounded bg-slate-900 border border-slate-800"
        >
          Close
        </button>
      </div>

      {/* Address Bar */}
      <div className="flex items-center justify-between p-2.5 rounded-lg bg-slate-900/90 border border-slate-800 font-mono text-xs">
        <span className="text-slate-300 truncate max-w-[220px]" title={address}>
          {shortenAddress(address, 10, 8)}
        </span>
        <div className="flex items-center gap-1.5">
          <button
            onClick={handleCopy}
            className="p-1.5 rounded hover:bg-slate-800 text-slate-400 hover:text-cyan-400 transition"
            title="Copy Address"
          >
            {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
          </button>
          <a
            href={`https://etherscan.io/address/${address}`}
            target="_blank"
            rel="noreferrer"
            className="p-1.5 rounded hover:bg-slate-800 text-slate-400 hover:text-cyan-400 transition"
            title="View on Etherscan"
          >
            <ExternalLink className="w-3.5 h-3.5" />
          </a>
        </div>
      </div>

      {/* Badges Row */}
      <div className="grid grid-cols-2 gap-2">
        <div className="p-2.5 rounded-lg bg-slate-900/60 border border-slate-800">
          <span className="text-[10px] text-slate-500 block">Entity Classification</span>
          <span className={`inline-block mt-1 px-2 py-0.5 text-xs font-semibold rounded border ${getEntityBadgeStyle(entity_type)}`}>
            {entity_type}
          </span>
        </div>

        <div className="p-2.5 rounded-lg bg-slate-900/60 border border-slate-800">
          <span className="text-[10px] text-slate-500 block">Trace Distance</span>
          <span className="inline-block mt-1 px-2 py-0.5 text-xs font-mono font-semibold text-cyan-300 bg-cyan-950/60 border border-cyan-800/50 rounded">
            Hop {hop_distance}
          </span>
        </div>
      </div>

      {/* Risk Assessment Gauge */}
      <div className="p-3.5 rounded-xl bg-slate-900/90 border border-slate-800 flex flex-col gap-2">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-1.5">
            <AlertTriangle className="w-4 h-4 text-amber-400" />
            <span className="text-xs font-bold text-white">Investigative Risk</span>
          </div>
          <span className={`px-2.5 py-0.5 text-xs font-bold rounded-full border shadow-sm ${getRiskBadgeStyle(risk.risk_level)}`}>
            {risk.risk_level} ({risk.score?.toFixed(1)})
          </span>
        </div>

        {/* Risk Score Progress Bar */}
        <div className="w-full bg-slate-800 rounded-full h-2 overflow-hidden mt-1">
          <div
            className={`h-full transition-all duration-500 ${
              risk.score >= 75 ? 'bg-red-500' : risk.score >= 50 ? 'bg-rose-500' : risk.score >= 25 ? 'bg-amber-500' : 'bg-emerald-500'
            }`}
            style={{ width: `${Math.min(100, Math.max(5, risk.score))}%` }}
          />
        </div>

        {/* Risk Reasons */}
        {risk.reasons && risk.reasons.length > 0 && (
          <div className="mt-2 text-xs space-y-1">
            <span className="text-[11px] font-semibold text-slate-400">Risk Factors:</span>
            <ul className="list-disc list-inside text-slate-300 space-y-0.5">
              {risk.reasons.map((r, idx) => (
                <li key={idx} className="truncate" title={r}>{r}</li>
              ))}
            </ul>
          </div>
        )}
      </div>

      {/* Attribution Confidence */}
      <div className="p-3 rounded-lg bg-slate-900/60 border border-slate-800 flex flex-col gap-1.5">
        <div className="flex justify-between items-center text-xs">
          <span className="text-slate-400">Attribution Confidence</span>
          <span className="font-mono text-cyan-400 font-bold">{confidencePct}%</span>
        </div>
        <div className="w-full bg-slate-800 rounded-full h-1.5 overflow-hidden">
          <div className="bg-cyan-400 h-full transition-all duration-300" style={{ width: `${confidencePct}%` }} />
        </div>
        {sources && sources.length > 0 && (
          <div className="text-[11px] text-slate-400 mt-1 flex items-center gap-1">
            <span className="text-slate-500">Sources:</span>
            <span className="font-mono text-slate-300">{sources.join(', ')}</span>
          </div>
        )}
      </div>

      {/* Supporting Evidence */}
      {evidence && (
        <div className="p-3 rounded-lg bg-slate-900/60 border border-slate-800 text-xs">
          <span className="text-[11px] font-semibold text-slate-400 block mb-1">Supporting Evidence</span>
          <p className="text-slate-300 italic leading-relaxed bg-slate-950/80 p-2 rounded border border-slate-800/60">
            "{evidence}"
          </p>
        </div>
      )}

    </div>
  );
}
