import React from 'react';
import { Shield, AlertOctagon, Users, Database, ArrowUpRight, TrendingUp, Filter } from 'lucide-react';
import { PieChart, Pie, Cell, ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, Legend } from 'recharts';
import { getDashboardMetrics } from '../services/api';
import { shortenAddress, getRiskBadgeStyle } from '../utils/formatters';

export default function DashboardView({ onSelectCase }) {
  const metrics = getDashboardMetrics();

  return (
    <div className="space-y-6">
      
      {/* Top Banner */}
      <div className="glass-panel p-6 rounded-2xl border border-slate-800 bg-gradient-to-r from-slate-900 via-slate-900/90 to-cyan-950/40 relative overflow-hidden">
        <div className="relative z-10 max-w-2xl">
          <span className="px-2.5 py-1 rounded-full text-xs font-semibold bg-cyan-500/20 text-cyan-300 border border-cyan-500/30 uppercase tracking-wider">
            SAHYOG Integration Support
          </span>
          <h2 className="text-2xl font-extrabold text-white mt-3 tracking-tight">
            Cybercrime Cryptocurrency Attribution & Tracing
          </h2>
          <p className="text-sm text-slate-300 mt-2 leading-relaxed">
            Automated transaction graph collection, multi-hop BFS tracing, entity attribution, and evidence-based risk scoring for law enforcement investigators.
          </p>
        </div>
        <div className="absolute right-6 top-1/2 -translate-y-1/2 opacity-10 pointer-events-none">
          <Shield className="w-64 h-64 text-cyan-400" />
        </div>
      </div>

      {/* Metrics Cards Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        
        <div className="glass-panel p-4 rounded-xl border border-slate-800 flex items-center justify-between">
          <div>
            <span className="text-xs text-slate-400">Total Cases</span>
            <h4 className="text-2xl font-bold text-white mt-1">{metrics.total_investigations}</h4>
            <span className="text-[11px] text-cyan-400 mt-1 inline-block">Active: {metrics.active_investigations}</span>
          </div>
          <div className="p-3 rounded-xl bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">
            <Shield className="w-6 h-6" />
          </div>
        </div>

        <div className="glass-panel p-4 rounded-xl border border-slate-800 flex items-center justify-between">
          <div>
            <span className="text-xs text-slate-400">High Risk Wallets</span>
            <h4 className="text-2xl font-bold text-red-400 mt-1">{metrics.high_risk_wallets}</h4>
            <span className="text-[11px] text-red-400/80 mt-1 inline-block">Priority Action Needed</span>
          </div>
          <div className="p-3 rounded-xl bg-red-500/10 text-red-400 border border-red-500/20">
            <AlertOctagon className="w-6 h-6" />
          </div>
        </div>

        <div className="glass-panel p-4 rounded-xl border border-slate-800 flex items-center justify-between">
          <div>
            <span className="text-xs text-slate-400">Attributed Entities</span>
            <h4 className="text-2xl font-bold text-blue-400 mt-1">{metrics.known_entities_count}</h4>
            <span className="text-[11px] text-blue-400/80 mt-1 inline-block">Local + Etherscan Tags</span>
          </div>
          <div className="p-3 rounded-xl bg-blue-500/10 text-blue-400 border border-blue-500/20">
            <Database className="w-6 h-6" />
          </div>
        </div>

        <div className="glass-panel p-4 rounded-xl border border-slate-800 flex items-center justify-between">
          <div>
            <span className="text-xs text-slate-400">Obfuscation Patterns</span>
            <h4 className="text-2xl font-bold text-amber-400 mt-1">4 Active</h4>
            <span className="text-[11px] text-amber-400/80 mt-1 inline-block">Splitting, Hopping, Layering</span>
          </div>
          <div className="p-3 rounded-xl bg-amber-500/10 text-amber-400 border border-amber-500/20">
            <TrendingUp className="w-6 h-6" />
          </div>
        </div>

      </div>

      {/* Analytics Recharts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        
        {/* Risk Distribution Donut Chart */}
        <div className="glass-panel p-5 rounded-xl border border-slate-800 flex flex-col justify-between">
          <div className="flex justify-between items-center mb-4">
            <div>
              <h3 className="text-base font-bold text-white">Investigative Risk Breakdown</h3>
              <p className="text-xs text-slate-400">Risk classification across active traced targets</p>
            </div>
            <span className="text-xs font-mono text-cyan-400">N = {metrics.total_investigations}</span>
          </div>
          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={metrics.risk_distribution}
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
        <div className="glass-panel p-5 rounded-xl border border-slate-800 flex flex-col justify-between">
          <div className="flex justify-between items-center mb-4">
            <div>
              <h3 className="text-base font-bold text-white">Traced Volume by Asset Type</h3>
              <p className="text-xs text-slate-400">ETH, Internal ETH & ERC-20 token movements</p>
            </div>
            <span className="text-xs font-mono text-slate-400">Mainnet V2</span>
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
      <div className="glass-panel rounded-xl border border-slate-800 p-5">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h3 className="text-base font-bold text-white">Recent Case Investigations</h3>
            <p className="text-xs text-slate-400">Select a case to inspect full trace graph & risk evidence</p>
          </div>
        </div>

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
                <tr key={item.id} className="hover:bg-slate-900/50 transition">
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
                      className="inline-flex items-center gap-1 px-3 py-1 text-xs font-sans font-medium rounded-lg bg-cyan-500/20 text-cyan-300 hover:bg-cyan-500/30 border border-cyan-500/40 transition"
                    >
                      Investigate <ArrowUpRight className="w-3 h-3" />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

    </div>
  );
}
