import React, { useState } from 'react';
import {
  AlertTriangle,
  ExternalLink,
  Copy,
  Check,
  Info,
  ArrowRightLeft,
  X,
  Target,
  ArrowUpRight,
  ArrowDownLeft
} from 'lucide-react';
import { shortenAddress, formatAmount } from '../../utils/formatters';
import RiskBadge from '../common/RiskBadge';
import EntityBadge from '../common/EntityBadge';

export default function AddressDrawer({
  selectedNode,
  graphData,
  onClose,
  onFocusNode,
  onTraceAsNewTarget
}) {
  const [copied, setCopied] = useState(false);
  const [activeTab, setActiveTab] = useState('intelligence'); // 'intelligence' | 'transactions'

  if (!selectedNode) {
    return (
      <div className="cyber-panel rounded-xl p-6 border border-slate-800/80 flex flex-col items-center justify-center text-center h-full text-slate-500">
        <div className="w-12 h-12 rounded-xl bg-slate-900 border border-slate-800 text-cyan-400 flex items-center justify-center mb-3">
          <Info className="w-6 h-6 opacity-70" />
        </div>
        <p className="text-sm font-bold text-slate-300">No Address Selected</p>
        <p className="text-xs text-slate-400 mt-1.5 max-w-xs leading-relaxed">
          Select any wallet or smart contract node in the transaction graph to inspect its attribution provenance, evidence trail, and risk breakdown.
        </p>
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

  const isUnknown = !entity || entity === 'Unknown';
  const confidencePct = Math.round((confidence || 0) * 100);

  const handleCopy = () => {
    navigator.clipboard.writeText(address);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  // Find incoming & outgoing transactions involving this address from the graph
  const addrLower = (address || '').toLowerCase();
  const rawGraph = graphData || {};
  const outboundTxs = rawGraph[address] || rawGraph[addrLower] || [];

  const inboundTxs = [];
  Object.entries(rawGraph).forEach(([fromAddr, txList]) => {
    if (fromAddr.toLowerCase() !== addrLower) {
      (txList || []).forEach((tx) => {
        if ((tx?.to || tx?.to_address || '').toLowerCase() === addrLower) {
          inboundTxs.push({ ...tx, from: fromAddr });
        }
      });
    }
  });

  const allTxsCount = outboundTxs.length + inboundTxs.length;

  return (
    <div className="cyber-panel rounded-xl p-5 border border-slate-800/80 flex flex-col gap-4 overflow-y-auto max-h-full h-full text-xs">
      {/* Header */}
      <div className="flex items-start justify-between border-b border-slate-800/80 pb-3">
        <div>
          <span className="text-[10px] font-mono font-bold tracking-wider text-cyan-400 uppercase block">
            Address Intelligence
          </span>
          <h3 className="text-base font-bold text-white mt-0.5 truncate max-w-[240px]" title={entity}>
            {isUnknown ? 'Unknown Entity' : entity}
          </h3>
        </div>
        <button
          onClick={onClose}
          className="p-1 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800/80 transition"
          title="Close drawer"
        >
          <X className="w-4 h-4" />
        </button>
      </div>

      {/* Tabs */}
      <div className="flex items-center bg-slate-950 p-1 rounded-lg border border-slate-800">
        <button
          onClick={() => setActiveTab('intelligence')}
          className={`flex-1 py-1 px-2 rounded text-[11px] font-semibold transition ${
            activeTab === 'intelligence'
              ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/40 shadow-sm'
              : 'text-slate-400 hover:text-slate-200'
          }`}
        >
          Forensics
        </button>
        <button
          onClick={() => setActiveTab('transactions')}
          className={`flex-1 py-1 px-2 rounded text-[11px] font-semibold transition flex items-center justify-center gap-1.5 ${
            activeTab === 'transactions'
              ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/40 shadow-sm'
              : 'text-slate-400 hover:text-slate-200'
          }`}
        >
          <span>Transactions</span>
          {allTxsCount > 0 && (
            <span className="text-[9px] font-mono px-1 py-0.2 rounded bg-slate-800 text-cyan-400">
              {allTxsCount}
            </span>
          )}
        </button>
      </div>

      {activeTab === 'intelligence' ? (
        <div className="space-y-4">
          {/* Address Box */}
          <div className="p-2.5 rounded-xl bg-slate-950/80 border border-slate-800 flex items-center justify-between font-mono">
            <span className="text-slate-300 truncate max-w-[190px]" title={address}>
              {shortenAddress(address, 10, 8)}
            </span>
            <div className="flex items-center gap-1">
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

          {/* Classification & Hop Grid */}
          <div className="grid grid-cols-2 gap-2">
            <div className="cyber-card p-2.5 rounded-lg border border-slate-800">
              <span className="text-[10px] text-slate-400 uppercase tracking-wider block mb-1">Entity Type</span>
              <EntityBadge type={entity_type} size="sm" />
            </div>

            <div className="cyber-card p-2.5 rounded-lg border border-slate-800">
              <span className="text-[10px] text-slate-400 uppercase tracking-wider block mb-1">Trace Distance</span>
              <span className="inline-block px-2 py-0.5 text-xs font-mono font-semibold text-cyan-300 bg-cyan-950/60 border border-cyan-800/50 rounded">
                Hop {hop_distance}
              </span>
            </div>
          </div>

          {/* Risk Assessment Gauge */}
          <div className="cyber-card p-3.5 rounded-xl border border-slate-800 flex flex-col gap-2">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-1.5">
                <AlertTriangle className="w-4 h-4 text-amber-400" />
                <span className="font-bold text-white uppercase text-[11px] tracking-wider">Investigative Risk</span>
              </div>
              <RiskBadge level={risk.risk_level} score={risk.score} size="xs" />
            </div>

            {/* Score Progress Bar */}
            <div className="w-full bg-slate-900 rounded-full h-2 overflow-hidden mt-1 border border-slate-800">
              <div
                className={`h-full transition-all duration-500 ${
                  (risk.score || 0) >= 75
                    ? 'bg-red-500'
                    : (risk.score || 0) >= 50
                    ? 'bg-rose-500'
                    : (risk.score || 0) >= 25
                    ? 'bg-amber-500'
                    : 'bg-emerald-500'
                }`}
                style={{ width: `${Math.min(100, Math.max(5, risk.score || 0))}%` }}
              />
            </div>

            {/* Risk Reasons */}
            {risk.reasons && risk.reasons.length > 0 && (
              <div className="mt-1 space-y-1">
                <span className="text-[10px] font-mono uppercase text-slate-400 font-semibold">Evidence Signals:</span>
                <ul className="text-slate-300 space-y-1 font-mono text-[11px]">
                  {risk.reasons.map((r, idx) => (
                    <li key={idx} className="flex items-start gap-1.5 leading-snug">
                      <span className="text-cyan-400 mt-0.5">&bull;</span>
                      <span className="break-words">{r}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>

          {/* Attribution Confidence */}
          <div className="cyber-card p-3 rounded-xl border border-slate-800 space-y-2">
            <div className="flex justify-between items-center text-xs">
              <span className="text-slate-400">Attribution Confidence</span>
              <span className="font-mono text-cyan-400 font-bold">{confidencePct}%</span>
            </div>
            <div className="w-full bg-slate-900 rounded-full h-1.5 overflow-hidden border border-slate-800">
              <div
                className="bg-cyan-400 h-full transition-all duration-300"
                style={{ width: `${confidencePct}%` }}
              />
            </div>

            {sources && sources.length > 0 && (
              <div className="text-[11px] text-slate-400 pt-1 flex items-center gap-1.5">
                <span className="text-slate-500">Sources:</span>
                <span className="font-mono text-slate-300">{sources.join(', ')}</span>
              </div>
            )}
          </div>

          {/* Supporting Evidence / Unknown state */}
          {evidence ? (
            <div className="cyber-card p-3 rounded-xl border border-slate-800 space-y-1">
              <span className="text-[10px] font-mono text-slate-400 uppercase font-semibold block">
                Evidence Provenance
              </span>
              <p className="text-slate-300 italic bg-slate-950/80 p-2.5 rounded-lg border border-slate-800/80 leading-relaxed font-mono text-[11px]">
                "{evidence}"
              </p>
            </div>
          ) : isUnknown ? (
            <div className="cyber-card p-3 rounded-xl border border-slate-800/80 text-slate-400 space-y-1">
              <span className="text-[10px] font-mono text-slate-400 uppercase font-semibold block">
                Unattributed On-Chain Wallet
              </span>
              <p className="text-[11px] leading-relaxed">
                No matching service provider, bridge, or known tag identified in public registries. Monitored through behavioral transfer patterns.
              </p>
            </div>
          ) : null}

          {/* Actions */}
          <div className="space-y-2 pt-2 border-t border-slate-800/80">
            {onFocusNode && (
              <button
                onClick={() => onFocusNode(address)}
                className="w-full py-2 px-3 rounded-lg bg-slate-800 hover:bg-slate-700 text-white font-medium flex items-center justify-center gap-2 transition"
              >
                <Target className="w-3.5 h-3.5 text-cyan-400" />
                Focus on Graph
              </button>
            )}

            {onTraceAsNewTarget && (
              <button
                onClick={() => onTraceAsNewTarget(address)}
                className="w-full py-2 px-3 rounded-lg bg-cyan-500/15 hover:bg-cyan-500/25 border border-cyan-500/30 text-cyan-300 font-medium flex items-center justify-center gap-2 transition"
              >
                <ArrowRightLeft className="w-3.5 h-3.5" />
                Investigate As New Target
              </button>
            )}
          </div>
        </div>
      ) : (
        /* Transactions List View */
        <div className="space-y-3">
          {allTxsCount === 0 ? (
            <div className="text-center py-10 text-slate-500 font-mono text-xs">
              No transactions recorded for this node in the current trace.
            </div>
          ) : (
            <div className="space-y-2 max-h-[460px] overflow-y-auto pr-1">
              {outboundTxs.map((tx, idx) => (
                <div
                  key={`out-${idx}`}
                  className="cyber-card p-2.5 rounded-lg border border-slate-800 space-y-1 font-mono text-[11px]"
                >
                  <div className="flex items-center justify-between text-rose-400">
                    <span className="flex items-center gap-1 font-bold">
                      <ArrowUpRight className="w-3.5 h-3.5" />
                      OUTBOUND
                    </span>
                    <span className="text-white font-bold">
                      {formatAmount(tx.amount, tx.symbol || tx.asset_type || 'ETH')}
                    </span>
                  </div>
                  <div className="text-slate-400 text-[10px] truncate">
                    To: {shortenAddress(tx.to || tx.to_address, 10, 8)}
                  </div>
                  {tx.hash && (
                    <div className="text-slate-500 text-[9px] truncate">
                      Tx: {tx.hash}
                    </div>
                  )}
                </div>
              ))}

              {inboundTxs.map((tx, idx) => (
                <div
                  key={`in-${idx}`}
                  className="cyber-card p-2.5 rounded-lg border border-slate-800 space-y-1 font-mono text-[11px]"
                >
                  <div className="flex items-center justify-between text-emerald-400">
                    <span className="flex items-center gap-1 font-bold">
                      <ArrowDownLeft className="w-3.5 h-3.5" />
                      INBOUND
                    </span>
                    <span className="text-white font-bold">
                      {formatAmount(tx.amount, tx.symbol || tx.asset_type || 'ETH')}
                    </span>
                  </div>
                  <div className="text-slate-400 text-[10px] truncate">
                    From: {shortenAddress(tx.from, 10, 8)}
                  </div>
                  {tx.hash && (
                    <div className="text-slate-500 text-[9px] truncate">
                      Tx: {tx.hash}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
