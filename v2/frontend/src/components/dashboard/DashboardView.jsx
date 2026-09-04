import React from 'react';
import {
  Shield,
  AlertOctagon,
  Database,
  ArrowUpRight,
  TrendingUp,
  Radio,
  PlusCircle
} from 'lucide-react';
import { PieChart, Pie, Cell, ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, Legend } from 'recharts';
import StatCard from '../common/StatCard';
import RiskBadge from '../common/RiskBadge';
import EntityBadge from '../common/EntityBadge';
import EmptyState from '../common/EmptyState';
import { deriveDashboardMetrics } from '../../services/api';
import { shortenAddress } from '../../utils/formatters';

export default function DashboardView({
  lastTraceResponse,
  apiLive,
  apiLatency,
  history = [],
  onSelectCase,
  onNewInvestigation
}) {
  const hasData = Boolean(lastTraceResponse || (history && history.length > 0));
  const metrics = deriveDashboardMetrics(lastTraceResponse, history);

  if (!hasData) {
    return (
      <div className="space-y-6 py-6">
        {/* Top Header Banner */}
        <div className="cyber-panel p-6 sm:p-8 rounded-2xl border border-cyan-500/20 relative overflow-hidden bg-gradient-to-r from-slate-900/90 via-slate-900/60 to-cyan-950/20">
          <div className="max-w-2xl space-y-3">
            <div className="flex items-center gap-2">
              <span className="px-2.5 py-0.5 rounded-full text-[11px] font-mono font-bold bg-cyan-500/15 text-cyan-300 border border-cyan-500/30 uppercase tracking-wider flex items-center gap-1.5">
                <Radio className="w-3 h-3 text-cyan-400" />
                Crypto Attribution Engine v2.0
              </span>
              <span className="px-2.5 py-0.5 rounded-full text-[11px] font-mono font-bold bg-slate-800 text-slate-400 border border-slate-700">
                Mainnet Ready
              </span>
            </div>
            <h2 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
              Blockchain Forensics & Attribution Workstation
            </h2>
            <p className="text-xs sm:text-sm text-slate-400 leading-relaxed">
              Automated multi-hop BFS graph tracing, smart contract attribution, evidence-weighted risk scoring, and structured obfuscation detection.
            </p>
          </div>
        </div>

        {/* Polished Empty State */}
        <EmptyState
          title="No investigations yet"
          description="Your forensic workstation is ready. Launch an investigation on a suspect Ethereum address to populate transaction graphs, risk breakdowns, and behavioral pattern analytics."
          actionLabel="Start First Investigation"
          onAction={onNewInvestigation}
        />
      </div>
    );
  }

  // Extract latest traced addresses
  const discovered = lastTraceResponse?.trace_results?.discovered_addresses || [];
  const latestAddresses = discovered.slice(0, 6);

  return (
    <div className="space-y-6">
      {/* 1. Top Section: Investigation Overview & Header */}
      <div className="cyber-panel p-6 rounded-2xl border border-slate-800/80 relative overflow-hidden bg-gradient-to-r from-slate-900/90 via-slate-900/70 to-cyan-950/25">
        <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4 relative z-10">
          <div>
            <div className="flex items-center gap-2 flex-wrap mb-2">
              <span className="px-2.5 py-0.5 rounded-full text-[11px] font-mono font-bold bg-cyan-500/20 text-cyan-300 border border-cyan-500/40 uppercase tracking-wider flex items-center gap-1.5 shadow-sm shadow-cyan-950/40">
                <Radio className="w-3 h-3 text-cyan-400 animate-pulse" />
                Investigation Overview
              </span>
              <span className="px-2.5 py-0.5 rounded-full text-[11px] font-mono font-bold bg-slate-800 text-slate-300 border border-slate-700">
                {apiLive ? 'API CONNECTED' : 'LOCAL ENGINE'}
              </span>
            </div>
            <h2 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
              Cryptocurrency Attribution Dashboard
            </h2>
            <p className="text-xs sm:text-sm text-slate-400 mt-1 max-w-xl leading-relaxed">
              Real-time forensic telemetry, risk distributions, and behavioral heuristics derived from active on-chain investigations.
            </p>
          </div>

          <button
            onClick={onNewInvestigation}
            className="px-5 py-2.5 rounded-xl bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-white font-bold text-xs shadow-lg shadow-cyan-950/50 flex items-center gap-2 transition transform active:scale-95 flex-shrink-0"
          >
            <PlusCircle className="w-4 h-4" />
            New Investigation
          </button>
        </div>
      </div>

      {/* 2. Key Metric Stat Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          label="Investigations"
          value={metrics.total_investigations}
          subtext={`${history.length} cases archived in ledger`}
          icon={Shield}
          variant="cyan"
        />

        <StatCard
          label="High Risk Wallets"
          value={metrics.high_risk_wallets}
          subtext="Flagged critical / high threat level"
          icon={AlertOctagon}
          variant="red"
          badge="ALERT"
        />

        <StatCard
          label="Attributed Addresses"
          value={metrics.known_entities_count}
          subtext="Resolved against known registries"
          icon={Database}
          variant="blue"
        />

        <StatCard
          label="Behavioral Patterns"
          value={metrics.obfuscation_patterns_count}
          subtext={
            metrics.obfuscation_pattern_labels.length > 0
              ? metrics.obfuscation_pattern_labels.slice(0, 2).join(', ')
              : 'None detected'
          }
          icon={TrendingUp}
          variant="amber"
        />
      </div>

      {/* 3. Analytics Visualizations Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Risk Distribution Donut Chart */}
        <div className="lg:col-span-6 cyber-panel p-5 rounded-2xl border border-slate-800/80 flex flex-col justify-between">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-base font-bold text-white tracking-wide">Risk Distribution</h3>
              <p className="text-xs text-slate-400">Classification across analyzed addresses</p>
            </div>
            <span className="text-xs font-mono text-cyan-400 px-2 py-0.5 rounded bg-slate-900 border border-slate-800">
              Score: {metrics.highest_risk_score ? metrics.highest_risk_score.toFixed(1) : '0.0'}/100
            </span>
          </div>

          <div className="h-60 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={metrics.risk_distribution}
                  cx="50%"
                  cy="50%"
                  innerRadius={55}
                  outerRadius={80}
                  paddingAngle={4}
                  dataKey="value"
                >
                  {metrics.risk_distribution.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} stroke="#060912" strokeWidth={2} />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#070b14',
                    borderColor: '#1e293b',
                    borderRadius: '8px',
                    color: '#fff',
                    fontSize: '11px'
                  }}
                  itemStyle={{ color: '#38bdf8' }}
                />
                <Legend verticalAlign="bottom" height={36} wrapperStyle={{ fontSize: '11px', color: '#94a3b8' }} />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Traced Volume by Asset Type */}
        <div className="lg:col-span-6 cyber-panel p-5 rounded-2xl border border-slate-800/80 flex flex-col justify-between">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-base font-bold text-white tracking-wide">Traced Volume by Asset</h3>
              <p className="text-xs text-slate-400">Financial flow breakdown by transfer token</p>
            </div>
            <span className="text-xs font-mono text-slate-400 px-2 py-0.5 rounded bg-slate-900 border border-slate-800">
              ETH / ERC20
            </span>
          </div>

          <div className="h-60 w-full">
            {metrics.asset_breakdown && metrics.asset_breakdown.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={metrics.asset_breakdown}>
                  <XAxis dataKey="asset" stroke="#64748b" fontSize={11} />
                  <YAxis stroke="#64748b" fontSize={11} />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#070b14',
                      borderColor: '#1e293b',
                      borderRadius: '8px',
                      color: '#fff',
                      fontSize: '11px'
                    }}
                  />
                  <Bar dataKey="volume" fill="#00f0ff" radius={[4, 4, 0, 0]}>
                    {metrics.asset_breakdown.map((entry, index) => (
                      <Cell key={`bar-${index}`} fill={entry.color} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-full flex items-center justify-center text-xs text-slate-500 font-mono">
                No transfer volume data available
              </div>
            )}
          </div>
        </div>
      </div>

      {/* 4. Split Grid: [Recent Investigations] & [Latest Traced Addresses] */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Recent Investigations Table */}
        <div className="lg:col-span-7 cyber-panel rounded-2xl border border-slate-800/80 p-5">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-base font-bold text-white">Recent Investigations</h3>
              <p className="text-xs text-slate-400">Active and archived case dossiers</p>
            </div>
            <span className="text-xs font-mono text-slate-500">{metrics.recent_investigations.length} Cases</span>
          </div>

          {metrics.recent_investigations.length === 0 ? (
            <div className="text-center py-8 text-xs text-slate-500 font-mono">
              No recent investigations
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs text-slate-300 font-mono">
                <thead className="bg-slate-950/80 text-slate-400 border-b border-slate-800 uppercase text-[10px]">
                  <tr>
                    <th className="px-3 py-2.5">Case ID</th>
                    <th className="px-3 py-2.5">Target Address</th>
                    <th className="px-3 py-2.5">Risk Level</th>
                    <th className="px-3 py-2.5 text-right">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60">
                  {metrics.recent_investigations.map((item) => (
                    <tr key={item.id} className="hover:bg-slate-900/50 transition">
                      <td className="px-3 py-3 font-bold text-cyan-400">{item.id}</td>
                      <td className="px-3 py-3 text-slate-200">
                        {shortenAddress(item.address, 8, 6)}
                      </td>
                      <td className="px-3 py-3">
                        <RiskBadge level={item.risk} score={item.score} size="xs" />
                      </td>
                      <td className="px-3 py-3 text-right">
                        <button
                          onClick={() => onSelectCase(item.address)}
                          className="inline-flex items-center gap-1 px-2.5 py-1 text-xs font-sans font-medium rounded-lg bg-cyan-500/15 text-cyan-300 hover:bg-cyan-500/25 border border-cyan-500/30 transition shadow-sm"
                        >
                          Workspace <ArrowUpRight className="w-3 h-3" />
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* Latest Traced Addresses Preview */}
        <div className="lg:col-span-5 cyber-panel rounded-2xl border border-slate-800/80 p-5 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-4">
              <div>
                <h3 className="text-base font-bold text-white">Latest Traced Nodes</h3>
                <p className="text-xs text-slate-400">Entity classifications in current scope</p>
              </div>
              <span className="text-xs font-mono text-cyan-400">{latestAddresses.length} Nodes</span>
            </div>

            {latestAddresses.length === 0 ? (
              <div className="text-center py-8 text-xs text-slate-500 font-mono">
                No addresses traced in active scope
              </div>
            ) : (
              <div className="space-y-2">
                {latestAddresses.map((node, idx) => (
                  <div
                    key={idx}
                    onClick={() => onSelectCase(node.address)}
                    className="p-2.5 rounded-xl bg-slate-950/60 border border-slate-800/80 hover:border-cyan-500/40 cursor-pointer transition flex items-center justify-between font-mono text-xs"
                  >
                    <div>
                      <span className="text-slate-200 font-semibold truncate block max-w-[170px]" title={node.address}>
                        {shortenAddress(node.address, 8, 6)}
                      </span>
                      <span className="text-[10px] text-slate-500 block">
                        Hop {node.hop_distance} &bull; {node.entity !== 'Unknown' ? node.entity : 'Unattributed'}
                      </span>
                    </div>

                    <div className="flex items-center gap-2">
                      <EntityBadge type={node.entity_type} size="xs" showIcon={false} />
                      <RiskBadge level={node.risk?.risk_level} score={node.risk?.score} size="xs" showIcon={false} />
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* System & API Status Box */}
          <div className="mt-4 pt-3 border-t border-slate-800/80 flex items-center justify-between text-[11px] font-mono text-slate-400">
            <div className="flex items-center gap-1.5">
              <span className={`w-2 h-2 rounded-full ${apiLive ? 'bg-emerald-400 animate-pulse' : 'bg-amber-400'}`} />
              <span>{apiLive ? 'API ONLINE (FastAPI)' : 'LOCAL DATASET'}</span>
            </div>
            {apiLatency !== null && (
              <span className="text-slate-500">Latency: {apiLatency}ms</span>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
