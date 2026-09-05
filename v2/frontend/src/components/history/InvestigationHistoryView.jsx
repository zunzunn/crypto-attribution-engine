import React, { useState } from 'react';
import { History, Search, Trash2, ArrowUpRight, Copy, Check, PlusCircle, Radio } from 'lucide-react';
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
    <div className="space-y-4">
      {/* Top Header */}
      <div className="bg-slate-950/80 border-b border-slate-800/30 p-4 sm:p-6 rounded-t-lg">
        <div className="flex items-center gap-2">
          <div className="p-2 rounded-xl bg-slate-800 text-slate-400">
            <History className="w-4 h-4" />
          </div>
          <div>
            <h2 className="text-xl font-bold text-slate-100 tracking-wide">Investigation Case Manager</h2>
            <p className="text-sm text-slate-500 mt-0.5">Archived forensic dossiers and multi-hop traces</p>
          </div>
        </div>

        <div className="flex items-center gap-2 w-full sm:w-auto">
          {history.length > 0 && (
            <button
              onClick={onClearAllHistory}
              className="px-3 py-1.5 rounded-lg bg-slate-900 hover:bg-slate-800/60 border border-slate-700/30 hover:border-slate-600/40 text-slate-400 hover:text-slate-200 text-xs font-medium flex items-center gap-1.5 transition"
              title="Clear all saved investigations"
            >
              <Trash2 className="w-3 h-3" />
              Clear All
            </button>
          )}

          <button
            onClick={onNewInvestigation}
            className="px-4 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-100 text-xs font-medium flex items-center gap-1.5 transition"
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
        <div className="space-y-3">
          {/* Filter Bar */}
          <div className="bg-slate-900/60 border border-slate-700/30 rounded-lg p-3.5">
            <div className="relative flex-1">
              <input
                type="text"
                placeholder="Search by Case ID, Target Address, or Entity..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full pl-9 pr-3 py-1.5 text-sm font-mono rounded-lg bg-slate-950 border border-slate-700 text-slate-300 placeholder-slate-500 focus:outline-none focus:border-slate-400 focus:ring-1 focus:ring-slate-500 transition"
              />
              <Search className="w-3 h-3 text-slate-500 absolute left-3 top-2" />
            </div>

            <div className="flex items-center gap-2 w-full sm:w-auto">
              <select
                value={riskFilter}
                onChange={(e) => setRiskFilter(e.target.value)}
                className="px-3 py-1.5 text-sm rounded-lg bg-slate-950 border border-slate-700 text-slate-300 focus:outline-none focus:border-slate-400 font-mono"
              >
                <option value="ALL">All Risk Levels</option>
                <option value="CRITICAL">Critical Risk</option>
                <option value="HIGH">High Risk</option>
                <option value="MEDIUM">Medium Risk</option>
                <option value="LOW">Low Risk</option>
              </select>

              <span className="text-sm font-mono text-slate-500">
                {filteredHistory.length} of {history.length} cases
              </span>
            </div>
          </div>

          {/* Case Management Table */}
          <div className="rounded-lg bg-slate-900 border border-slate-700/30 overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm text-slate-400 font-mono">
                <thead className="bg-slate-950/60 text-slate-400 border-b border-slate-700/30 uppercase text-[9px] tracking-wider">
                  <tr>
                    <th className="px-4 py-2.5">Case ID</th>
                    <th className="px-4 py-2.5">Target Address</th>
                    <th className="px-4 py-2.5">Risk Assessment</th>
                    <th className="px-4 py-2.5">Data Source</th>
                    <th className="px-4 py-2.5">Discovered</th>
                    <th className="px-4 py-2.5">Date</th>
                    <th className="px-4 py-2.5 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/30">
                  {filteredHistory.map((item) => (
                    <tr key={item.case_id} className="hover:bg-slate-950/50 transition">
                      <td className="px-4 py-3 font-medium text-slate-300">{item.case_id}</td>

                      <td className="px-4 py-3">
                        <div className="flex items-center gap-1.5">
                          <span className="font-semibold text-slate-200" title={item.target_address}>
                            {shortenAddress(item.target_address, 8, 6)}
                          </span>
                          <button
                            onClick={() => handleCopy(item.target_address, item.case_id)}
                            className="p-1 rounded hover:bg-slate-800 text-slate-300 hover:text-slate-100 transition"
                            title="Copy Address"
                          >
                            {copiedId === item.case_id ? (
                              <Check className="w-2.5 h-2.5 text-emerald-400" />
                            ) : (
                              <Copy className="w-2.5 h-2.5" />
                            )
                          }
                          </button>
                        </div>
                        {item.entity && item.entity !== 'Unknown' && (
                          <span className="text-[9px] text-slate-500 block">Tag: {item.entity}</span>
                        )}
                      </td>

                      <td className="px-4 py-3">
                        <RiskBadge level={item.risk_level} score={item.risk_score} size="xs" />
                      </td>

                      <td className="px-4 py-3">
                        <span
                          className={`inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[9px] font-semibold border ${
                            item.is_live
                              ? 'bg-slate-800/70 text-slate-300 border-slate-500/40'
                              : 'bg-slate-900 text-slate-400 border-slate-700/30'
                          }`}
                        >
                          <Radio className="w-2 h-2" />
                          {item.is_live ? 'Mainnet Live' : 'Local'}
                        </span>
                      </td>

                      <td className="px-4 py-3 text-slate-400">
                        <div>{item.discovered_count || 1} addresses</div>
                        <span className="text-[8px] text-slate-500">{item.max_hops || 2} Hops</span>
                      </td>

                      <td className="px-4 py-3 text-slate-500 text-[9px]">
                        {formatTimestamp(item.created_at)}
                      </td>

                      <td className="px-4 py-3 text-right">
                        <div className="flex items-center justify-end gap-1">
                          <button
                            onClick={() => onOpenCase(item)}
                            className="inline-flex items-center gap-1 px-2 py-1 text-xs font-medium rounded bg-slate-800/60 text-slate-300 hover:bg-slate-700/70 border border-slate-700/30 transition shadow-sm"
                            title="Open in Workspace"
                          >
                            Open <ArrowUpRight className="w-2.5 h-2.5" />
                          </button>
                          <button
                            onClick={() => onDeleteCase(item.case_id)}
                            className="p-1 rounded-lg text-slate-500 hover:text-amber-400 hover:bg-slate-800 transition"
                            title="Delete case"
                          >
                            <Trash2 className="w-2.5 h-2.5" />
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