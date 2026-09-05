import React from 'react';
import { Layers, Zap, ArrowRight, Info, Clock, GitBranch, Split, Workflow } from 'lucide-react';
import { shortenAddress } from '../../utils/formatters';

export default function BehavioralPanel({ patterns, onSelectAddress }) {
  const patternSummary = patterns?.summary || {};
  const fanOutEvents = patterns?.fan_out_events || [];
  const fanInEvents = patterns?.fan_in_events || [];
  const rapidHoppingEvents = patterns?.rapid_hopping_events || [];
  const layeringEvents = patterns?.layering_events || [];

  const totalDetected = patternSummary.total_patterns_detected || 0;

  if (totalDetected === 0) {
    return null;
  }

  return (
    <section className="pt-3">
      {/* Header */}
      <div className="border-b border-slate-700/30 pb-3 mb-3">
        <div className="flex items-center gap-2">
          <div className="p-1 rounded bg-slate-800 text-slate-400">
            <Workflow className="w-3 h-3" />
          </div>
          <div>
            <h3 className="text-sm font-semibold text-slate-300 uppercase tracking-wider">Behavioral Obfuscation Intelligence</h3>
            <p className="text-[9px] text-slate-500">
              Heuristic anomaly detection for structured money laundering patterns
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2 text-[9px] text-slate-500">
          {totalDetected} Finding{totalDetected !== 1 ? 's' : ''} Detected
        </div>
      </div>

      <div className="space-y-2">
        {/* Fan-Out / Splitting Findings */}
        {fanOutEvents.map((evt, idx) => (
          <div
            key={`fanout-${idx}`}
            className="rounded-lg bg-slate-800 p-3 border border-slate-700/30 mb-2"
          >
            <div className="flex items-center justify-between mb-1">
              <div className="flex items-center gap-1.5">
                <div className="p-1 rounded bg-amber-500/10 text-amber-400">
                  <Split className="w-3 h-3" />
                </div>
                <span className="font-medium text-slate-200">FAN-OUT STRUCTURING</span>
              </div>
              <span className="text-[8px] font-mono font-bold rounded bg-amber-500/20 text-amber-300 border border-amber-500/30 uppercase">
                High Risk
              </span>
            </div>

            <p className="text-[9px] text-slate-400 leading-relaxed">
              {evt.description || `Address split funds across ${evt.recipient_count || evt.recipients?.length || 3} separate counterparties.`}
            </p>

            {/* Source & Recipients */}
            {evt.recipients && evt.recipients.length > 0 && (
              <div className="mt-1.5 text-[9px] text-slate-400">
                <span className="block mb-0.5">Recipients:</span>
                {evt.recipients.slice(0, 4).map((r, rIdx) => (
                  <button
                    key={rIdx}
                    onClick={() => onSelectAddress && onSelectAddress(r)}
                    className="px-1 py-0.5 rounded bg-slate-900 text-slate-300 hover:border-slate-600/40 transition"
                  >
                    {shortenAddress(r, 6, 4)}
                  </button>
                ))}
              </div>
            )}
          </div>
        ))}

        {/* Fan-In / Consolidation Findings */}
        {fanInEvents.map((evt, idx) => (
          <div
            key={`fanin-${idx}`}
            className="rounded-lg bg-slate-800 p-3 border border-slate-700/30 mb-2"
          >
            <div className="flex items-center justify-between mb-1">
              <div className="flex items-center gap-1.5">
                <div className="p-1 rounded bg-slate-800 text-slate-400">
                  <GitBranch className="w-3 rotate-180" />
                </div>
                <span className="font-medium text-slate-200">FAN-IN CONSOLIDATION</span>
              </div>
              <span className="text-[8px] font-mono font-bold rounded bg-slate-800 text-slate-300 border border-slate-700/30 uppercase">
                Medium Signal
              </span>
            </div>

            <p className="text-[9px] text-slate-400 leading-relaxed">
              {evt.description || `Multiple unassociated addresses consolidated assets into a single collector wallet.`}
            </p>
          </div>
        ))}

        {/* Rapid Hopping Findings */}
        {rapidHoppingEvents.map((evt, idx) => (
          <div
            key={`hopping-${idx}`}
            className="rounded-lg bg-slate-800 p-3 border border-slate-700/30 mb-2"
          >
            <div className="flex items-center justify-between mb-1">
              <div className="flex items-center gap-1.5">
                <div className="p-1 rounded bg-slate-800 text-slate-400">
                  <Zap className="w-3" />
                </div>
                <span className="font-medium text-slate-200">RAPID WALLET HOPPING</span>
              </div>
              <span className="text-[8px] font-mono font-bold rounded bg-slate-800 text-slate-300 border border-slate-700/30 uppercase">
                Critical Timing
              </span>
            </div>

            <p className="text-[9px] text-slate-400 leading-relaxed">
              {evt.description || `Rapid pass-through transfer observed within low latency window.`}
            </p>

            {/* Hop Sequence */}
            <div className="mt-1.5 text-[8px] text-slate-400">
              <button
                onClick={() => onSelectAddress && onSelectAddress(evt.hop_1_from)}
                className="px-1 py-0.5 rounded bg-slate-900 text-slate-300 hover:border-slate-600/40 transition"
              >
                {shortenAddress(evt.hop_1_from, 6, 4)}
              </button>
              <span className="mx-0.5 text-[8px] text-slate-500">→</span>
              <button
                onClick={() => onSelectAddress && onSelectAddress(evt.intermediate_address)}
                className="px-1 py-0.5 rounded bg-slate-900 text-slate-300 hover:border-slate-600/40 transition font-bold"
              >
                {shortenAddress(evt.intermediate_address, 6, 4)}
              </button>
              <span className="mx-0.5 text-[8px] text-slate-500">→</span>
              <button
                onClick={() => onSelectAddress && onSelectAddress(evt.hop_2_to)}
                className="px-1 py-0.5 rounded bg-slate-900 text-slate-300 hover:border-slate-600/40 transition"
              >
                {shortenAddress(evt.hop_2_to, 6, 4)}
              </button>
              {evt.time_delta_seconds !== undefined && (
                <span className="ml-auto text-[8px] text-slate-500">
                  <Clock className="w-2 h-2 text-slate-500" />
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
            className="rounded-lg bg-slate-800 p-3 border border-slate-700/30 mb-2"
          >
            <div className="flex items-center justify-between mb-1">
              <div className="flex items-center gap-1.5">
                <div className="p-1 rounded bg-slate-800 text-slate-400">
                  <Layers className="w-3" />
                </div>
                <span className="font-medium text-slate-200">MULTI-HOP LAYERING</span>
              </div>
              <span className="text-[8px] font-mono font-bold rounded bg-slate-800 text-slate-300 border border-slate-700/30 uppercase">
                Layering {evt.max_hop_depth || 3}+ Hops
              </span>
            </div>

            <p className="text-[9px] text-slate-400 leading-relaxed">
              {evt.description || `Funds traversed multiple sequential intermediary wallets to obfuscate audit trail.`}
            </p>

            {/* Terminal Nodes */}
            {evt.addresses && evt.addresses.length > 0 && (
              <div className="mt-1.5 text-[8px] text-slate-400">
                <span className="block mb-0.5">Terminal Nodes:</span>
                {evt.addresses.map((addr, aIdx) => (
                  <button
                    key={aIdx}
                    onClick={() => onSelectAddress && onSelectAddress(addr)}
                    className="px-1 py-0.5 rounded bg-slate-900 text-slate-300 hover:border-slate-600/40 transition"
                  >
                    {shortenAddress(addr, 6, 4)}
                  </button>
                ))}
              </div>
            )}
          </div>
        ))}
      </div>
    </section>
  );
}