import React from 'react';
import {
  Shield,
  AlertOctagon,
  Database,
  ArrowUpRight,
  TrendingUp,
  PlusCircle,
  FileCheck
} from 'lucide-react';
import { shortenAddress } from '../../utils/formatters';
import RiskBadge from '../common/RiskBadge';

export default function DashboardView({
  lastTraceResponse,
  apiLive,
  apiLatency,
  history = [],
  onSelectCase,
  onNewInvestigation
}) {
  const highRiskCount = history.filter(
    (item) => (item.risk_level || '').toUpperCase() === 'CRITICAL' || (item.risk_level || '').toUpperCase() === 'HIGH'
  ).length;

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Top Header Banner */}
      <div className="bg-surface border border-border rounded-2xl p-6 sm:p-7 backdrop-blur-md shadow-sm flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold text-primary tracking-tight">
            Forensic Intelligence Workspace
          </h2>
          <p className="text-sm text-secondary mt-1">
            Law-enforcement grade multi-hop blockchain tracing and entity attribution
          </p>
        </div>
        <button
          onClick={onNewInvestigation}
          className="px-4 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-500 text-white text-sm font-medium transition flex items-center gap-2 shadow-sm self-start sm:self-auto"
        >
          <PlusCircle className="w-4 h-4" />
          <span>New Investigation</span>
        </button>
      </div>

      {/* Overview Stats Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-surface border border-border rounded-2xl p-5 shadow-sm space-y-2 backdrop-blur-md">
          <div className="flex items-center justify-between">
            <span className="text-xs font-mono uppercase tracking-wider text-secondary">Investigations</span>
            <div className="p-2 rounded-xl bg-blue-500/10 text-blue-500">
              <Shield className="w-4 h-4" />
            </div>
          </div>
          <div>
            <div className="text-3xl font-extrabold text-primary">{history.length}</div>
            <span className="text-xs text-secondary">cases archived in local database</span>
          </div>
        </div>

        <div className="bg-surface border border-border rounded-2xl p-5 shadow-sm space-y-2 backdrop-blur-md">
          <div className="flex items-center justify-between">
            <span className="text-xs font-mono uppercase tracking-wider text-secondary">Threat Flagged</span>
            <div className="p-2 rounded-xl bg-rose-500/10 text-rose-500">
              <AlertOctagon className="w-4 h-4" />
            </div>
          </div>
          <div>
            <div className="text-3xl font-extrabold text-rose-500">{highRiskCount}</div>
            <span className="text-xs text-secondary">high or critical risk suspects</span>
          </div>
        </div>

        <div className="bg-surface border border-border rounded-2xl p-5 shadow-sm space-y-2 backdrop-blur-md">
          <div className="flex items-center justify-between">
            <span className="text-xs font-mono uppercase tracking-wider text-secondary">Attributed</span>
            <div className="p-2 rounded-xl bg-purple-500/10 text-purple-500">
              <Database className="w-4 h-4" />
            </div>
          </div>
          <div>
            <div className="text-3xl font-extrabold text-primary">
              {history.length > 0 ? history.length : 0}
            </div>
            <span className="text-xs text-secondary">targets mapped to known entities</span>
          </div>
        </div>

        <div className="bg-surface border border-border rounded-2xl p-5 shadow-sm space-y-2 backdrop-blur-md">
          <div className="flex items-center justify-between">
            <span className="text-xs font-mono uppercase tracking-wider text-secondary">Engine Status</span>
            <div className={`p-2 rounded-xl ${apiLive ? 'bg-emerald-500/10 text-emerald-500' : 'bg-amber-500/10 text-amber-500'}`}>
              <TrendingUp className="w-4 h-4" />
            </div>
          </div>
          <div>
            <div className="text-xl font-bold text-primary mt-1">
              {apiLive ? 'ONLINE' : 'LOCAL CACHED'}
            </div>
            <span className="text-xs text-secondary">
              {apiLatency !== null ? `${apiLatency}ms latency` : 'FastAPI local mock'}
            </span>
          </div>
        </div>
      </div>

      {/* Recent Investigations Table */}
      <div className="bg-surface border border-border rounded-2xl overflow-hidden shadow-sm backdrop-blur-md">
        <div className="px-6 py-4 border-b border-border flex items-center justify-between">
          <div>
            <h3 className="text-base font-semibold text-primary">Recent Cases</h3>
            <p className="text-xs text-secondary">Archived forensic investigation dossiers</p>
          </div>
          <span className="text-xs font-mono text-secondary">{history.length} cases</span>
        </div>

        {history.length === 0 ? (
          <div className="p-12 text-center text-secondary space-y-2">
            <FileCheck className="w-8 h-8 mx-auto opacity-50" />
            <p className="text-sm font-medium">No archived cases yet.</p>
            <p className="text-xs">Start a trace on any Ethereum wallet address to generate forensic evidence.</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm font-mono">
              <thead className="bg-surface-subtle text-secondary border-b border-border uppercase text-[10px] tracking-wider">
                <tr>
                  <th className="px-6 py-3">Case ID</th>
                  <th className="px-6 py-3">Target Address</th>
                  <th className="px-6 py-3">Risk Assessment</th>
                  <th className="px-6 py-3">Attribution</th>
                  <th className="px-6 py-3 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {history.map((item) => {
                  const caseId = item.case_id || item.id;
                  const addr = item.target_address || item.address;
                  const riskLevel = item.risk_level || item.risk || 'Low';
                  const riskScore = item.risk_score ?? item.score ?? 0;
                  const entity = item.entity || 'Unknown';

                  return (
                    <tr key={caseId || addr} className="hover:bg-surface-subtle transition">
                      <td className="px-6 py-3.5 font-medium text-primary">{caseId}</td>
                      <td className="px-6 py-3.5 text-secondary">
                        {shortenAddress(addr, 10, 8)}
                      </td>
                      <td className="px-6 py-3.5">
                        <RiskBadge level={riskLevel} score={riskScore} size="xs" />
                      </td>
                      <td className="px-6 py-3.5 text-secondary text-xs">
                        {entity}
                      </td>
                      <td className="px-6 py-3.5 text-right">
                        <button
                          onClick={() => onSelectCase(addr)}
                          className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-lg bg-surface border border-border text-primary hover:bg-surface-subtle transition shadow-sm"
                        >
                          <span>Open</span>
                          <ArrowUpRight className="w-3 h-3" />
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}