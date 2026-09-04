import React, { useState, useEffect } from 'react';
import { CheckCircle2, Loader2, Circle, Cpu } from 'lucide-react';
import { shortenAddress } from '../../utils/formatters';

const STAGES = [
  { id: 'fetch', label: 'Fetching transactions', desc: 'Querying on-chain transaction history & transfer logs' },
  { id: 'graph', label: 'Building transaction graph', desc: 'Constructing directed adjacency matrix of fund movements' },
  { id: 'trace', label: 'Tracing wallet flow', desc: 'Traversing multi-hop BFS paths from target root' },
  { id: 'attrib', label: 'Attributing addresses', desc: 'Matching against known VASP, mixer, and bridge registries' },
  { id: 'behavior', label: 'Detecting behavior', desc: 'Evaluating splitting, consolidation, hopping, and layering heuristics' },
  { id: 'risk', label: 'Calculating risk', desc: 'Computing evidence-weighted risk metrics and hop penalties' },
  { id: 'gen', label: 'Generating investigation', desc: 'Compiling interactive graph and forensic intelligence dossier' },
];

export default function LoadingProgress({ targetAddress, isLive = false, maxHops = 2 }) {
  const [activeStageIndex, setActiveStageIndex] = useState(0);

  useEffect(() => {
    // Stage timer progression across stages while the request is running
    const interval = setInterval(() => {
      setActiveStageIndex((prev) => (prev < STAGES.length - 1 ? prev + 1 : prev));
    }, 750);

    return () => clearInterval(interval);
  }, []);

  return (
    <div className="cyber-panel rounded-2xl p-6 sm:p-8 border border-cyan-500/30 max-w-xl mx-auto shadow-2xl shadow-cyan-950/40 relative overflow-hidden">
      {/* Background Accent Grid */}
      <div className="absolute top-0 right-0 w-48 h-48 bg-gradient-to-bl from-cyan-500/10 to-transparent rounded-bl-full pointer-events-none" />

      {/* Header */}
      <div className="flex items-center justify-between border-b border-slate-800/80 pb-4 mb-5">
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-xl bg-cyan-500/15 text-cyan-400 border border-cyan-500/30 animate-pulse">
            <Cpu className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-base font-bold text-white tracking-wide">
              Forensic Attribution In Progress
            </h3>
            <p className="text-xs font-mono text-cyan-400 mt-0.5">
              Target: {shortenAddress(targetAddress, 10, 8)} &bull; {maxHops} Hops Depth
            </p>
          </div>
        </div>
        <span className="text-[11px] font-mono px-2.5 py-1 rounded bg-slate-900 border border-slate-800 text-slate-400">
          {isLive ? 'LIVE CHAIN' : 'LOCAL ENGINE'}
        </span>
      </div>

      {/* Progress Stepper */}
      <div className="space-y-3.5 my-4">
        {STAGES.map((stage, idx) => {
          const isDone = idx < activeStageIndex;
          const isCurrent = idx === activeStageIndex;
          const isPending = idx > activeStageIndex;

          return (
            <div
              key={stage.id}
              className={`flex items-start gap-3 transition-all duration-300 ${
                isPending ? 'opacity-35' : isCurrent ? 'opacity-100 scale-[1.01]' : 'opacity-70'
              }`}
            >
              <div className="mt-0.5 flex-shrink-0">
                {isDone && <CheckCircle2 className="w-4 h-4 text-emerald-400" />}
                {isCurrent && <Loader2 className="w-4 h-4 text-cyan-400 animate-spin" />}
                {isPending && <Circle className="w-4 h-4 text-slate-600" />}
              </div>
              <div className="flex-1">
                <div className="flex items-center justify-between">
                  <span
                    className={`text-xs font-semibold ${
                      isCurrent
                        ? 'text-cyan-300 font-bold'
                        : isDone
                        ? 'text-slate-200'
                        : 'text-slate-500'
                    }`}
                  >
                    {stage.label}
                  </span>
                  {isCurrent && (
                    <span className="text-[10px] font-mono text-cyan-400 animate-pulse">
                      Analyzing...
                    </span>
                  )}
                  {isDone && (
                    <span className="text-[10px] font-mono text-emerald-400">
                      Done
                    </span>
                  )}
                </div>
                <p className="text-[11px] text-slate-400 mt-0.5 leading-normal">
                  {stage.desc}
                </p>
              </div>
            </div>
          );
        })}
      </div>

      {/* Footer Info */}
      <div className="mt-6 pt-4 border-t border-slate-800/80 flex items-center justify-between text-[11px] text-slate-400 font-mono">
        <span>Stage {activeStageIndex + 1} of {STAGES.length}</span>
        <span className="text-cyan-400">Autonomous Evidence Pipeline</span>
      </div>
    </div>
  );
}
