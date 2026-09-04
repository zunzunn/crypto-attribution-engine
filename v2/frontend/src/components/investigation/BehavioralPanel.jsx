import React from 'react';
import {
  GitBranch,
  Layers,
  Zap,
  ArrowRight,
  Info,
  Clock,
  Split,
  Workflow
} from 'lucide-react';
import { shortenAddress } from '../../utils/formatters';

export default function BehavioralPanel({ patterns, onSelectAddress }) {
  const patternSummary = patterns?.summary || {};
  const fanOutEvents = patterns?.fan_out_events || [];
  const fanInEvents = patterns?.fan_in_events || [];
  const rapidHoppingEvents = patterns?.rapid_hopping_events || [];
  const layeringEvents = patterns?.layering_events || [];

  const totalDetected = patternSummary.total_patterns_detected || 0;

  return (
    <div className="cyber-panel rounded-xl p-5 border border-slate-800/80 space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-slate-800/80 pb-3">
        <div className="flex items-center gap-2">
          <div className="p-1.5 rounded-lg bg-amber-500/15 text-amber-400 border border-amber-500/30">
            <Workflow className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-white uppercase tracking-wider">
              Behavioral Obfuscation Intelligence
            </h3>
            <p className="text-[11px] text-slate-400">
              Heuristic anomaly detection for structured money laundering patterns
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-slate-900 border border-slate-800 text-slate-300">
            {totalDetected} Finding{totalDetected !== 1 ? 's' : ''} Detected
          </span>
        </div>
      </div>

      {totalDetected === 0 ? (
        <div className="text-center py-6 text-slate-500 font-mono text-xs flex flex-col items-center justify-center">
          <Info className="w-6 h-6 opacity-40 mb-1.5" />
          <span>No obfuscation or rapid transfer anomalies detected in the current trace path.</span>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3.5">
          {/* Fan-Out / Splitting Findings */}
          {fanOutEvents.map((evt, idx) => (
            <div
              key={`fanout-${idx}`}
              className="cyber-card p-4 rounded-xl border border-amber-500/30 bg-amber-950/10 space-y-2.5"
            >
              <div className="flex items-start justify-between">
                <div className="flex items-center gap-2">
                  <div className="p-1.5 rounded-lg bg-amber-500/20 text-amber-300">
                    <Split className="w-4 h-4" />
                  </div>
                  <div>
                    <h4 className="text-xs font-bold text-amber-200">
                      FAN-OUT STRUCTURING (Splitting)
                    </h4>
                    <span className="text-[10px] font-mono text-amber-400/80">
                      Smurfing / Partition Anomaly
                    </span>
                  </div>
                </div>
                <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded bg-amber-500/20 text-amber-300 border border-amber-500/40 uppercase">
                  High Risk Signal
                </span>
              </div>

              <p className="text-xs text-slate-300 leading-relaxed">
                {evt.description || `Address split funds across ${evt.recipient_count || evt.recipients?.length || 3} separate counterparties.`}
              </p>

              {/* Source & Affected Recipients */}
              <div className="text-[11px] font-mono space-y-1 pt-1 border-t border-amber-500/20">
                <div className="flex items-center gap-2 text-slate-400">
                  <span className="text-slate-500">Origin:</span>
                  <button
                    onClick={() => onSelectAddress && onSelectAddress(evt.address)}
                    className="text-cyan-300 hover:underline font-bold"
                  >
                    {shortenAddress(evt.address, 8, 6)}
                  </button>
                  {evt.total_outbound_amount && (
                    <span className="text-slate-300">({evt.total_outbound_amount} ETH)</span>
                  )}
                </div>

                {evt.recipients && evt.recipients.length > 0 && (
                  <div className="flex flex-wrap items-center gap-1.5 mt-1">
                    <span className="text-slate-500">Recipients:</span>
                    {evt.recipients.slice(0, 4).map((r, rIdx) => (
                      <button
                        key={rIdx}
                        onClick={() => onSelectAddress && onSelectAddress(r)}
                        className="text-[10px] px-1.5 py-0.5 rounded bg-slate-900/90 text-cyan-400 border border-slate-700/80 hover:border-cyan-400 transition"
                      >
                        {shortenAddress(r, 6, 4)}
                      </button>
                    ))}
                  </div>
                )}
              </div>
            </div>
          ))}

          {/* Fan-In / Consolidation Findings */}
          {fanInEvents.map((evt, idx) => (
            <div
              key={`fanin-${idx}`}
              className="cyber-card p-4 rounded-xl border border-amber-500/30 bg-amber-950/10 space-y-2.5"
            >
              <div className="flex items-start justify-between">
                <div className="flex items-center gap-2">
                  <div className="p-1.5 rounded-lg bg-amber-500/20 text-amber-300">
                    <GitBranch className="w-4 h-4 rotate-180" />
                  </div>
                  <div>
                    <h4 className="text-xs font-bold text-amber-200">
                      FAN-IN CONSOLIDATION
                    </h4>
                    <span className="text-[10px] font-mono text-amber-400/80">
                      Multi-Source Funneling
                    </span>
                  </div>
                </div>
                <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded bg-amber-500/20 text-amber-300 border border-amber-500/40 uppercase">
                  Medium Signal
                </span>
              </div>

              <p className="text-xs text-slate-300 leading-relaxed">
                {evt.description || `Multiple unassociated addresses consolidated assets into a single collector wallet.`}
              </p>
            </div>
          ))}

          {/* Rapid Hopping Findings */}
          {rapidHoppingEvents.map((evt, idx) => (
            <div
              key={`hopping-${idx}`}
              className="cyber-card p-4 rounded-xl border border-red-500/30 bg-red-950/10 space-y-2.5"
            >
              <div className="flex items-start justify-between">
                <div className="flex items-center gap-2">
                  <div className="p-1.5 rounded-lg bg-red-500/20 text-red-300">
                    <Zap className="w-4 h-4" />
                  </div>
                  <div>
                    <h4 className="text-xs font-bold text-red-200">
                      RAPID WALLET HOPPING
                    </h4>
                    <span className="text-[10px] font-mono text-red-400/80">
                      High-Velocity Pass-Through
                    </span>
                  </div>
                </div>
                <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded bg-red-500/20 text-red-300 border border-red-500/40 uppercase">
                  Critical Timing
                </span>
              </div>

              <p className="text-xs text-slate-300 leading-relaxed">
                {evt.description || `Rapid pass-through transfer observed within low latency window.`}
              </p>

              {/* Hop Sequence */}
              <div className="text-[11px] font-mono pt-1 border-t border-red-500/20 flex flex-wrap items-center gap-1.5 text-slate-300">
                <button
                  onClick={() => onSelectAddress && onSelectAddress(evt.hop_1_from)}
                  className="px-1.5 py-0.5 rounded bg-slate-900 border border-slate-700 text-cyan-300 hover:border-cyan-400"
                >
                  {shortenAddress(evt.hop_1_from, 6, 4)}
                </button>
                <ArrowRight className="w-3 h-3 text-slate-500" />
                <button
                  onClick={() => onSelectAddress && onSelectAddress(evt.intermediate_address)}
                  className="px-1.5 py-0.5 rounded bg-slate-900 border border-red-700/60 text-red-300 font-bold hover:border-red-400"
                >
                  {shortenAddress(evt.intermediate_address, 6, 4)}
                </button>
                <ArrowRight className="w-3 h-3 text-slate-500" />
                <button
                  onClick={() => onSelectAddress && onSelectAddress(evt.hop_2_to)}
                  className="px-1.5 py-0.5 rounded bg-slate-900 border border-slate-700 text-cyan-300 hover:border-cyan-400"
                >
                  {shortenAddress(evt.hop_2_to, 6, 4)}
                </button>
                {evt.time_delta_seconds !== undefined && (
                  <span className="ml-auto text-[10px] text-slate-400 flex items-center gap-1">
                    <Clock className="w-3 h-3 text-slate-500" />
                    {evt.time_delta_seconds}s interval
                  </span>
                )}
              </div>
            </div>
          ))}

          {/* Multi-Hop Layering Findings */}
          {layeringEvents.map((evt, idx) => (
            <div
              key={`layering-${idx}`}
              className="cyber-card p-4 rounded-xl border border-purple-500/30 bg-purple-950/10 space-y-2.5"
            >
              <div className="flex items-start justify-between">
                <div className="flex items-center gap-2">
                  <div className="p-1.5 rounded-lg bg-purple-500/20 text-purple-300">
                    <Layers className="w-4 h-4" />
                  </div>
                  <div>
                    <h4 className="text-xs font-bold text-purple-200">
                      MULTI-HOP LAYERING
                    </h4>
                    <span className="text-[10px] font-mono text-purple-400/80">
                      Sequential Chain Distance Anomaly
                    </span>
                  </div>
                </div>
                <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded bg-purple-500/20 text-purple-300 border border-purple-500/40 uppercase">
                  Layering {evt.max_hop_depth || 3}+ Hops
                </span>
              </div>

              <p className="text-xs text-slate-300 leading-relaxed">
                {evt.description || `Funds traversed multiple sequential intermediary wallets to obfuscate audit trail.`}
              </p>

              {evt.addresses && evt.addresses.length > 0 && (
                <div className="flex flex-wrap items-center gap-1.5 pt-1 border-t border-purple-500/20 text-[11px] font-mono">
                  <span className="text-slate-500">Terminal Nodes:</span>
                  {evt.addresses.map((addr, aIdx) => (
                    <button
                      key={aIdx}
                      onClick={() => onSelectAddress && onSelectAddress(addr)}
                      className="px-1.5 py-0.5 rounded bg-slate-900 border border-slate-700 text-purple-300 hover:border-purple-400"
                    >
                      {shortenAddress(addr, 6, 4)}
                    </button>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
