import React from 'react';
import { Shield, AlertOctagon, Users, Database, ArrowUpRight, TrendingUp, Radio } from 'lucide-react';
import { PieChart, Pie, Cell, ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, Legend } from 'recharts';
import { EMPTY_DASHBOARD_METRICS, deriveDashboardMetrics } from '../services/api';
import { shortenAddress, getRiskBadgeStyle } from '../utils/formatters';

export default function DashboardView({ onSelectCase, lastTraceResponse, apiLive }) {
  const hasTrace = Boolean(lastTraceResponse);
  const metrics = hasTrace ? deriveDashboardMetrics(lastTraceResponse) : EMPTY_DASHBOARD_METRICS;
  const isDemoFallback = hasTrace && apiLive === false;
  const targetAddress = hasTrace ? (lastTraceResponse.target_address || '0x') : null;

  return (
    <div className="space-y-6">

      {/* Top Cybernetic Banner with Animated Radar Scanner */}
      <div className="glass-panel p-6 rounded-2xl border border-cyan-500/20 relative overflow-hidden bg-gradient-to-r from-slate-900/80 via-slate-900/60 to-cyan-950/30">

        {/* Radar Scanner Visual Effect */}
        <div className="absolute -right-16 -top-16 w-80 h-80 rounded-full border border-cyan-500/10 pointer-events-none flex items-center justify-center">
          <div className="w-56 h-56 rounded-full border border-cyan-500/15 flex items-center justify-center">
            <div className="w-32 h-32 rounded-full border border-cyan-500/20" />
          </div>
          <div className="absolute inset-0 radar-beam bg-gradient-to-tr from-transparent via-cyan-500/10 to-transparent rounded-full" />
        </div>

        <div className="relative z-10 max-w-2xl">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-cyan-500/20 text-cyan-300 border border-cyan-500/40 uppercase tracking-wider flex items-center gap-1.5 shadow-sm shadow-cyan-950">
              <Radio className="w-3 h-3 animate-pulse text-cyan-400" />
              Realtime Forensics Grid Active
            </span>
            {isDemoFallback && (
              <span className="px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-amber-500/25 text-amber-200 border border-amber-500/50 uppercase tracking-wider">
                DEMO / MOCK FALLBACK
              </span>
            )}
            {!hasTrace && (
              <span className="px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-slate-700/40 text-slate-200 border border-slate-500/50 uppercase tracking-wider">
                NO INVESTIGATION DATA
              </span>
            )}
          </div>
          <h2 className="text-2xl sm:text-3xl font-extrabold text-white mt-3 tracking-tight">
            Cybercrime Cryptocurrency Attribution Engine
          </h2>
          <p className="text-sm text-slate-300 mt-2 leading-relaxed">
            Automated multi-hop BFS tracing, entity attribution, and evidence-based risk scoring with 3D cyberspace network visualization.
          </p>
        </div>
      </div>

      {/* 3D Perspective Tilt Metric Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 perspective-container">

        <div className="glass-panel tilt-card p-5 rounded-xl border border-slate-800/80 flex items-center justify-between cursor-default">
          <div>
            <span className="text-xs text-slate-400 font-medium">Total Investigations</span>
            <h4 className="text-3xl font-extrabold text-white mt-1">{metrics.total_investigations}</h4>
            <span className="text-[11px] text-cyan-400 font-mono mt-1 inline-block">Active: {metrics.active_investigations}</span>
          </div>
          <div className="p-3.5 rounded-xl bg-cyan-500/10 text-cyan-400 border border-cyan-500/30 shadow-lg shadow-cyan-950/40">
            <Shield className="w-6 h-6" />
          </div>
        </div>

        <div className="glass-panel tilt-card p-5 rounded-xl border border-slate-800/80 flex items-center justify-between cursor-default">
          <div>
            <span className="text-xs text-slate-400 font-medium">High Risk Wallets</span>
            <h4 className="text-3xl font-extrabold text-red-400 mt-1">{metrics.high_risk_wallets}</h4>
            <span className="text-[11px] text-red-400/80 font-mono mt-1 inline-block">From Current Trace</span>
          </div>
          <div className="p-3.5 rounded-xl bg-red-500/10 text-red-400 border border-red-500/30 shadow-lg shadow-red-950/40">
            <AlertOctagon className="w-6 h-6" />
          </div>
        </div>

        <div className="glass-panel tilt-card p-5 rounded-xl border border-slate-800/80 flex items-center justify-between cursor-default">
          <div>
            <span className="text-xs text-slate-400 font-medium">Attributed Entities</span>
            <h4 className="text-3xl font-extrabold text-blue-400 mt-1">{metrics.known_entities_count}</h4>
            <span className="text-[11px] text-blue-400/80 font-mono mt-1 inline-block">From Current Trace</span>
          </div>
          <div className="p-3.5 rounded-xl bg-blue-500/10 text-blue-400 border border-blue-500/30 shadow-lg shadow-blue-950/40">
            <Database className="w-6 h-6" />
          </div>
        </div>

        <div className="glass-panel tilt-card p-5 rounded-xl border border-slate-800/80 flex items-center justify-between cursor-default">
          <div>
            <span className="text-xs text-slate-400 font-medium">Obfuscation Patterns</span>
            <h4 className="text-3xl font-extrabold text-amber-400 mt-1">
              {metrics.obfuscation_patterns_count} Active
            </h4>
            <span className="text-[11px] text-amber-400/80 font-mono mt-1 inline-block">
              {metrics.obfuscation_pattern_labels.length > 0
                ? metrics.obfuscation_pattern_labels.join(', ')
                : 'None Detected'}
            </span>
          </div>
          <div className="p-3.5 rounded-xl bg-amber-500/10 text-amber-400 border border-amber-500/30 shadow-lg shadow-amber-950/40">
            <TrendingUp className="w-6 h-6" />
          </div>
        </div>

      </div>

      {/* Analytics Recharts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">

        {/* Risk Distribution Donut Chart */}
        <div className="glass-panel p-5 rounded-xl border border-slate-800/80 flex flex-col justify-between">
          <div className="flex justify-between items-center mb-4">
            <div>
              <h3 className="text-base font-bold text-white">Investigative Risk Breakdown</h3>
              <p className="text-xs text-slate-400">
                {hasTrace ? 'Classification across traced addresses' : 'No investigation data'}
              </p>
            </div>
            <span className="text-xs font-mono text-cyan-400">
              {hasTrace ? `N = ${metrics.total_investigations}` : 'N = 0'}
            </span>
          </div>
          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={hasTrace ? metrics.risk_distribution : []}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={85}
                  paddingAngle={5}
                  dataKey="value"
                >
                  {metrics.risk_distribution.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} stroke="#0a0e17" strokeWidth={2} />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px', color: '#fff' }}
                  itemStyle={{ color: '#38bdf8' }}
                />
                <Legend verticalAlign="bottom" height={36} wrapperStyle={{ fontSize: '12px', color: '#94a3b8' }} />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Asset Type Breakdown Bar Chart */}
        <div className="glass-panel p-5 rounded-xl border border-slate-800/80 flex flex-col justify-between">
          <div className="flex justify-between items-center mb-4">
            <div>
              <h3 className="text-base font-bold text-white">Traced Volume by Asset Type</h3>
              <p className="text-xs text-slate-400">
                {hasTrace ? 'From current returned transfers' : 'No investigation data'}
              </p>
            </div>
            <span className="text-xs font-mono text-slate-400">
              {hasTrace ? (lastTraceResponse.live_data ? 'Mainnet LIVE' : 'Mainnet V2') : '—'}
            </span>
          </div>
          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={metrics.asset_breakdown}>
                <XAxis dataKey="asset" stroke="#64748b" fontSize={11} />
                <YAxis stroke="#64748b" fontSize={11} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px', color: '#fff' }}
                />
                <Bar dataKey="volume" fill="#00f0ff" radius={[4, 4, 0, 0]}>
                  {metrics.asset_breakdown.map((entry, index) => (
                    <Cell key={`bar-${index}`} fill={entry.color} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

      </div>

      {/* Recent Case Investigations Table */}
      <div className="glass-panel rounded-xl border border-slate-800/80 p-5">
        <div className="flex items-center justify-between mb-4 flex-wrap gap-2">
          <div>
            <h3 className="text-base font-bold text-white">Current Case Investigation</h3>
            <p className="text-xs text-slate-400">
              {hasTrace
                ? `Single active investigation${targetAddress ? ` for ${shortenAddress(targetAddress, 8, 6)}` : ''}`
                : 'No investigation data — run a trace to populate the dashboard'}
            </p>
          </div>
        </div>

        {!hasTrace ? (
          <div className="text-center py-10 text-xs text-slate-500 font-mono">
            No investigation data
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs text-slate-300">
              <thead className="bg-slate-900/80 text-slate-400 border-b border-slate-800 uppercase font-mono text-[10px]">
                <tr>
                  <th className="px-4 py-3">Case ID</th>
                  <th className="px-4 py-3">Target Address</th>
                  <th className="px-4 py-3">Entity Attribution</th>
                  <th className="px-4 py-3">Max Hops</th>
                  <th className="px-4 py-3">Risk Level</th>
                  <th className="px-4 py-3">Score</th>
                  <th className="px-4 py-3 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 font-mono">
                {metrics.recent_investigations.map((item) => (
                  <tr key={item.id} className="hover:bg-slate-900/60 transition">
                    <td className="px-4 py-3 font-bold text-cyan-400">{item.id}</td>
                    <td className="px-4 py-3 text-slate-200">{shortenAddress(item.address, 10, 6)}</td>
                    <td className="px-4 py-3 font-sans text-slate-300">{item.entity}</td>
                    <td className="px-4 py-3 text-slate-400">{item.hops} Hops</td>
                    <td className="px-4 py-3">
                      <span className={`px-2 py-0.5 text-[11px] font-bold rounded border ${getRiskBadgeStyle(item.risk)}`}>
                        {item.risk}
                      </span>
                    </td>
                    <td className="px-4 py-3 font-bold text-white">{item.score.toFixed(1)}</td>
                    <td className="px-4 py-3 text-right">
                      <button
                        onClick={() => onSelectCase(item.address)}
                        className="inline-flex items-center gap-1 px-3 py-1 text-xs font-sans font-medium rounded-lg bg-cyan-500/20 text-cyan-300 hover:bg-cyan-500/30 border border-cyan-500/40 transition shadow-sm"
                      >
                        3D Trace <ArrowUpRight className="w-3 h-3" />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

    </div>
  );
}