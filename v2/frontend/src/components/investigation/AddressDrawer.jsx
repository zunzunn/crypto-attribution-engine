import React, { useState } from 'react';
import {
  AlertTriangle,
  ExternalLink,
  Copy,
  Check,
  Info,
  ArrowRightLeft,
  ArrowUpRight,
  ArrowDownLeft,
  Target,
  X,
  Shield
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
  const [activeTab, setActiveTab] = useState('intelligence');

  if (!selectedNode) {
    return (
      <div className="h-full rounded-xl bg-slate-950/80 border border-slate-800/50 backdrop-blur-md p-6 flex flex-col items-center justify-center text-center text-slate-500">
        <div className="w-12 h-12 rounded-xl bg-slate-900 border border-slate-800 text-slate-400 flex items-center justify-center mb-3 shadow-inner">
          <Info className="w-5 h-5 opacity-70" />
        </div>
        <h4 className="text-sm font-semibold text-slate-300">No Address Selected</h4>
        <p className="text-xs text-slate-500 mt-1.5 max-w-xs leading-relaxed">
          Select any node in the transaction graph to inspect its attribution provenance, risk score, and transaction flow.
        </p>
      </div>
    );
  }

  const {
    address = '',
    entity = 'Unknown',
    entity_type = 'Unknown',
    confidence = 0,
    hop_distance = 0,
    evidence = '',
    risk = { score: 0, risk_level: 'Low', reasons: [] }
  } = selectedNode;

  const isUnknown = !entity || entity === 'Unknown';
  const confidencePct = Math.round((confidence || 0) * 100);

  const handleCopy = (e) => {
    e.stopPropagation();
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
    <div className="h-full rounded-xl bg-slate-950/90 border border-slate-800/50 backdrop-blur-md flex flex-col overflow-hidden text-xs">
      {/* Header */}
      <div className="p-3.5 border-b border-slate-800/50 flex items-center justify-between bg-slate-950/60">
        <div className="min-w-0 pr-2">
          <span className="text-[10px] font-mono uppercase tracking-wider text-slate-500 block">Node Intelligence</span>
          <h3 className="text-sm font-bold text-slate-100 truncate" title={entity}>
            {isUnknown ? 'Unknown Entity' : entity}
          </h3>
        </div>
        <button
          onClick={onClose}
          className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition flex-shrink-0"
          title="Deselect Node"
        >
          <X className="w-3.5 h-3.5" />
        </button>
      </div>

      {/* Tabs */}
      <div className="p-1 border-b border-slate-800/50 flex items-center bg-slate-900/50 gap-1">
        <button
          onClick={() => setActiveTab('intelligence')}
          className={`flex-1 py-1.5 px-2 rounded-lg text-xs font-medium transition text-center ${
            activeTab === 'intelligence'
              ? 'bg-slate-800 text-slate-200 shadow-sm'
              : 'text-slate-400 hover:text-slate-200'
          }`}
        >
          Forensics
        </button>
        <button
          onClick={() => setActiveTab('transactions')}
          className={`flex-1 py-1.5 px-2 rounded-lg text-xs font-medium transition text-center flex items-center justify-center gap-1.5 ${
            activeTab === 'transactions'
              ? 'bg-slate-800 text-slate-200 shadow-sm'
              : 'text-slate-400 hover:text-slate-200'
          }`}
        >
          <span>Transactions</span>
          {allTxsCount > 0 && (
            <span className="text-[9px] font-mono px-1.5 py-0.2 rounded-full bg-slate-700 text-slate-300">
              {allTxsCount}
            </span>
          )}
        </button>
      </div>

      {/* Main Content Body */}
      {activeTab === 'intelligence' ? (
        <div className="flex-1 overflow-y-auto p-3.5 space-y-3">
          {/* Address Box */}
          <div className="p-2.5 rounded-lg bg-slate-900/70 border border-slate-800/60 flex items-center justify-between">
            <span className="font-mono text-xs text-slate-300 truncate mr-2" title={address}>
              {shortenAddress(address, 10, 8)}
            </span>
            <div className="flex items-center gap-1 flex-shrink-0">
              <button
                onClick={handleCopy}
                className="p-1 rounded hover:bg-slate-800 text-slate-400 hover:text-slate-200 transition"
                title="Copy Address"
              >
                {copied ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />}
              </button>
              <a
                href={`https://etherscan.io/address/${address}`}
                target="_blank"
                rel="noreferrer"
                className="p-1 rounded hover:bg-slate-800 text-slate-400 hover:text-slate-200 transition"
                title="View on Etherscan"
              >
                <ExternalLink className="w-3 h-3" />
              </a>
            </div>
          </div>

          {/* Classification & Hop Grid */}
          <div className="grid grid-cols-2 gap-2">
            <div className="rounded-lg bg-slate-900/50 border border-slate-800/50 p-2.5">
              <span className="text-[9px] text-slate-500 uppercase font-mono tracking-wider block mb-1">Classification</span>
              <EntityBadge type={entity_type} size="sm" />
            </div>

            <div className="rounded-lg bg-slate-900/50 border border-slate-800/50 p-2.5">
              <span className="text-[9px] text-slate-500 uppercase font-mono tracking-wider block mb-1">BFS Distance</span>
              <span className="inline-block px-2 py-0.5 text-xs font-mono font-semibold text-slate-300 bg-slate-800 rounded">
                Hop {hop_distance}
              </span>
            </div>
          </div>

          {/* Risk Assessment */}
          <div className="rounded-lg bg-slate-900/60 border border-slate-800/50 p-3 space-y-2">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-1.5">
                <AlertTriangle className="w-3.5 h-3.5 text-amber-400" />
                <span className="font-semibold text-slate-200 text-xs">Risk Assessment</span>
              </div>
              <RiskBadge level={risk.risk_level} score={risk.score} size="xs" />
            </div>

            {/* Score Progress Bar */}
            <div className="w-full bg-slate-800 rounded-full h-1.5 overflow-hidden">
              <div
                className={`h-full transition-all duration-300 ${
                  (risk.score || 0) >= 75
                    ? 'bg-rose-500'
                    : (risk.score || 0) >= 50
                    ? 'bg-rose-400'
                    : (risk.score || 0) >= 25
                    ? 'bg-amber-400'
                    : 'bg-emerald-400'
                }`}
                style={{ width: `${Math.min(100, Math.max(5, risk.score || 0))}%` }}
              />
            </div>

            {/* Risk Reasons */}
            {risk.reasons && risk.reasons.length > 0 && (
              <div className="mt-2 space-y-1">
                <span className="text-[9px] uppercase font-mono text-slate-500">Evidence Signals:</span>
                <ul className="text-slate-400 space-y-1 font-mono text-[10px]">
                  {risk.reasons.map((r, idx) => (
                    <li key={idx} className="flex items-start gap-1.5 leading-tight">
                      <span className="text-slate-600 mt-0.5">&bull;</span>
                      <span className="break-words">{r}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>

          {/* Attribution Confidence */}
          <div className="rounded-lg bg-slate-900/50 border border-slate-800/50 p-2.5">
            <div className="flex justify-between items-center text-xs mb-1.5">
              <span className="text-slate-400">Attribution Confidence</span>
              <span className="font-mono text-slate-200 font-bold">{confidencePct}%</span>
            </div>
            <div className="w-full bg-slate-800 rounded-full h-1.5 overflow-hidden">
              <div
                className="bg-blue-500 h-full transition-all duration-300"
                style={{ width: `${confidencePct}%` }}
              />
            </div>
          </div>

          {/* Evidence */}
          {evidence ? (
            <div className="rounded-lg bg-slate-900/50 border border-slate-800/50 p-2.5">
              <span className="text-[9px] font-mono uppercase text-slate-500 font-semibold block mb-1">
                Evidence Provenance
              </span>
              <p className="text-slate-400 text-[10px] leading-relaxed italic">{evidence}</p>
            </div>
          ) : isUnknown ? (
            <div className="rounded-lg bg-slate-900/50 border border-slate-800/50 p-2.5">
              <span className="text-[9px] font-mono uppercase text-slate-500 font-semibold block mb-1">
                Unattributed On-Chain Wallet
              </span>
              <p className="text-slate-500 text-[10px] leading-relaxed">
                No matching service provider, bridge, or known tag identified in public registries. Monitored through behavioral transfer heuristics.
              </p>
            </div>
          ) : null}

          {/* Actions */}
          <div className="pt-2 space-y-1.5 border-t border-slate-800/50">
            {onFocusNode && (
              <button
                onClick={() => onFocusNode(address)}
                className="w-full py-2 px-3 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-100 font-medium flex items-center justify-center gap-1.5 transition text-xs"
              >
                <Target className="w-3.5 h-3.5 text-slate-300" />
                Focus on Graph
              </button>
            )}

            {onTraceAsNewTarget && (
              <button
                onClick={() => onTraceAsNewTarget(address)}
                className="w-full py-2 px-3 rounded-lg bg-slate-900 hover:bg-slate-850 border border-slate-800 text-slate-300 hover:text-white font-medium flex items-center justify-center gap-1.5 transition text-xs"
              >
                <ArrowRightLeft className="w-3.5 h-3.5" />
                Investigate As New Target
              </button>
            )}
          </div>
        </div>
      ) : (
        /* Transactions Tab */
        <div className="flex-1 overflow-y-auto p-3.5">
          {allTxsCount === 0 ? (
            <div className="py-12 text-center text-slate-500 text-xs">
              No transactions recorded for this node in the current trace.
            </div>
          ) : (
            <div className="space-y-2">
              {outboundTxs.map((tx, idx) => (
                <div
                  key={`out-${idx}`}
                  className="rounded-lg bg-slate-900/70 p-2.5 border border-slate-800/50 font-mono text-[10px] space-y-0.5"
                >
                  <div className="flex items-center justify-between text-amber-400">
                    <span className="flex items-center gap-1 font-bold">
                      <ArrowUpRight className="w-3 h-3" />
                      OUTBOUND
                    </span>
                    <span className="font-bold text-slate-200">
                      {formatAmount(tx.amount, tx.symbol || tx.asset_type || 'ETH')}
                    </span>
                  </div>
                  <div className="text-slate-400 truncate">
                    To: {shortenAddress(tx.to || tx.to_address, 8, 6)}
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
                  className="rounded-lg bg-slate-900/70 p-2.5 border border-slate-800/50 font-mono text-[10px] space-y-0.5"
                >
                  <div className="flex items-center justify-between text-emerald-400">
                    <span className="flex items-center gap-1 font-bold">
                      <ArrowDownLeft className="w-3 h-3" />
                      INBOUND
                    </span>
                    <span className="font-bold text-slate-200">
                      {formatAmount(tx.amount, tx.symbol || tx.asset_type || 'ETH')}
                    </span>
                  </div>
                  <div className="text-slate-400 truncate">
                    From: {shortenAddress(tx.from, 8, 6)}
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