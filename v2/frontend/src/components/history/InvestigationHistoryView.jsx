import React, { useState } from 'react';
import {
  History,
  Search,
  Trash2,
  ArrowUpRight,
  Copy,
  Check,
  PlusCircle,
  Radio
} from 'lucide-react';
import { shortenAddress, formatTimestamp } from '../../utils/formatters';
import RiskBadge from '../common/RiskBadge';
import EmptyState from '../common/EmptyState';

export default function InvestigationHistoryView({
  history = [],
  onOpenCase,
  onDeleteCase,
  onClearAllHistory,
  onNewInvestigation
}) {
  const [searchTerm, setSearchTerm] = useState('');
  const [riskFilter, setRiskFilter] = useState('ALL');
  const [copiedId, setCopiedId] = useState(null);

  const handleCopy = (addr, id) => {
    navigator.clipboard.writeText(addr);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  const filteredHistory = history.filter((item) => {
    const term = searchTerm.toLowerCase();
    const matchesSearch =
      (item.case_id || '').toLowerCase().includes(term) ||
      (item.target_address || '').toLowerCase().includes(term) ||
      (item.entity || '').toLowerCase().includes(term);

    const matchesRisk =
      riskFilter === 'ALL' ||
      (item.risk_level || '').toUpperCase() === riskFilter.toUpperCase();

    return matchesSearch && matchesRisk;
  });

  return (
    <div className="space-y-6">
      {/* Top Header */}
      <div className="cyber-panel p-5 sm:p-6 rounded-2xl border border-slate-800/80 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <div className="p-2 rounded-xl bg-cyan-500/10 text-cyan-400 border border-cyan-500/30">
              <History className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-xl font-bold text-white tracking-wide">
                Investigation Case Manager
              </h2>
              <p className="text-xs text-slate-400 mt-0.5">
                Archived forensic dossiers, multi-hop traces, and evidentiary snapshots
              </p>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-2 w-full sm:w-auto">
          {history.length > 0 && (
            <button
              onClick={onClearAllHistory}
              className="px-3 py-1.5 rounded-xl bg-slate-900 hover:bg-red-500/15 border border-slate-700/80 hover:border-red-500/40 text-slate-400 hover:text-red-300 text-xs font-medium flex items-center gap-1.5 transition"
              title="Clear all saved investigations"
            >
              <Trash2 className="w-3.5 h-3.5" />
              Clear All
            </button>
          )}

          <button
            onClick={onNewInvestigation}
            className="px-4 py-1.5 rounded-xl bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-white font-bold text-xs shadow-md shadow-cyan-950/50 flex items-center gap-1.5 transition"
          >
            <PlusCircle className="w-3.5 h-3.5" />
            New Case
          </button>
        </div>
      </div>

      {history.length === 0 ? (
        <EmptyState
          title="No investigations archived"
          description="Your case history is currently empty. Run an investigation trace to begin indexing on-chain suspect wallets, graph paths, and risk scores."
          actionLabel="Start Investigation"
          onAction={onNewInvestigation}
        />
      ) : (
        <div className="space-y-4">
          {/* Filter Bar */}
          <div className="cyber-panel p-3.5 rounded-xl border border-slate-800/80 flex flex-col sm:flex-row items-center justify-between gap-3">
            <div className="relative flex-1 w-full sm:w-80">
              <input
                type="text"
                placeholder="Search by Case ID, Target Address, or Entity..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full pl-9 pr-4 py-1.5 text-xs font-mono rounded-lg bg-slate-950 border border-slate-700/80 text-white placeholder-slate-500 focus:outline-none focus:border-cyan-500"
              />
              <Search className="w-3.5 h-3.5 text-slate-500 absolute left-3 top-2" />
            </div>

            <div className="flex items-center gap-2 w-full sm:w-auto">
              <select
                value={riskFilter}
                onChange={(e) => setRiskFilter(e.target.value)}
                className="px-3 py-1.5 text-xs rounded-lg bg-slate-950 border border-slate-700/80 text-slate-300 focus:outline-none focus:border-cyan-500 font-mono"
              >
                <option value="ALL">All Risk Levels</option>
                <option value="CRITICAL">Critical Risk</option>
                <option value="HIGH">High Risk</option>
                <option value="MEDIUM">Medium Risk</option>
                <option value="LOW">Low Risk</option>
              </select>

              <span className="text-xs font-mono text-slate-500">
                {filteredHistory.length} of {history.length} cases
              </span>
            </div>
          </div>

          {/* Case Management Table */}
          <div className="cyber-panel rounded-xl border border-slate-800/80 overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs text-slate-300 font-mono">
                <thead className="bg-slate-950/80 text-slate-400 border-b border-slate-800 uppercase text-[10px] tracking-wider">
                  <tr>
                    <th className="px-4 py-3">Case ID</th>
                    <th className="px-4 py-3">Target Address</th>
                    <th className="px-4 py-3">Risk Assessment</th>
                    <th className="px-4 py-3">Data Source</th>
                    <th className="px-4 py-3">Discovered</th>
                    <th className="px-4 py-3">Date</th>
                    <th className="px-4 py-3 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60">
                  {filteredHistory.map((item) => (
                    <tr key={item.case_id} className="hover:bg-slate-900/50 transition">
                      {/* Case ID */}
                      <td className="px-4 py-3 font-bold text-cyan-400">
                        {item.case_id}
                      </td>

                      {/* Target Address */}
                      <td className="px-4 py-3">
                        <div className="flex items-center gap-1.5">
                          <span className="text-white font-semibold" title={item.target_address}>
                            {shortenAddress(item.target_address, 8, 6)}
                          </span>
                          <button
                            onClick={() => handleCopy(item.target_address, item.case_id)}
                            className="p-1 rounded hover:bg-slate-800 text-slate-400 hover:text-cyan-300 transition"
                            title="Copy Address"
                          >
                            {copiedId === item.case_id ? (
                              <Check className="w-3 h-3 text-emerald-400" />
                            ) : (
                              <Copy className="w-3 h-3" />
                            )}
                          </button>
                        </div>
                        {item.entity && item.entity !== 'Unknown' && (
                          <span className="text-[10px] text-slate-500 block">
                            Tag: {item.entity}
                          </span>
                        )}
                      </td>

                      {/* Risk */}
                      <td className="px-4 py-3">
                        <RiskBadge level={item.risk_level} score={item.risk_score} size="xs" />
                      </td>

                      {/* Live / Local */}
                      <td className="px-4 py-3">
                        <span
                          className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-semibold border ${
                            item.is_live
                              ? 'bg-cyan-500/15 text-cyan-300 border-cyan-500/30'
                              : 'bg-slate-800 text-slate-400 border-slate-700'
                          }`}
                        >
                          <Radio className="w-2.5 h-2.5" />
                          {item.is_live ? 'Mainnet Live' : 'Local'}
                        </span>
                      </td>

                      {/* Discovered & Hops */}
                      <td className="px-4 py-3 text-slate-300">
                        <div>{item.discovered_count || 1} addresses</div>
                        <span className="text-[10px] text-slate-500">{item.max_hops || 2} Hops</span>
                      </td>

                      {/* Date */}
                      <td className="px-4 py-3 text-slate-400 text-[11px]">
                        {formatTimestamp(item.created_at)}
                      </td>

                      {/* Actions */}
                      <td className="px-4 py-3 text-right">
                        <div className="flex items-center justify-end gap-1.5">
                          <button
                            onClick={() => onOpenCase(item)}
                            className="inline-flex items-center gap-1 px-2.5 py-1 text-xs font-sans font-semibold rounded-lg bg-cyan-500/15 text-cyan-300 hover:bg-cyan-500/25 border border-cyan-500/30 transition shadow-sm"
                            title="Open in Workspace"
                          >
                            Open <ArrowUpRight className="w-3 h-3" />
                          </button>
                          <button
                            onClick={() => onDeleteCase(item.case_id)}
                            className="p-1 rounded-lg text-slate-500 hover:text-red-400 hover:bg-slate-800 transition"
                            title="Delete case"
                          >
                            <Trash2 className="w-3.5 h-3.5" />
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
