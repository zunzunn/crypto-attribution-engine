import React from 'react';
import { ShieldQuestion, PlusCircle } from 'lucide-react';

export default function EmptyState({
  icon: Icon = ShieldQuestion,
  title = "No investigations yet",
  description = "Launch a forensic trace on a suspect Ethereum address to begin entity attribution, risk analysis, and transaction graph generation.",
  actionLabel = "Start Investigation",
  onAction = null,
  secondaryAction = null
}) {
  return (
    <div className="cyber-panel rounded-2xl p-10 sm:p-14 border border-slate-800/80 flex flex-col items-center justify-center text-center max-w-xl mx-auto my-8">
      <div className="w-16 h-16 rounded-2xl bg-cyan-500/10 border border-cyan-500/20 text-cyan-400 flex items-center justify-center mb-5 shadow-lg shadow-cyan-950/40">
        <Icon className="w-8 h-8" />
      </div>

      <h3 className="text-xl font-bold text-white tracking-tight">{title}</h3>
      <p className="text-xs sm:text-sm text-slate-400 mt-2.5 leading-relaxed max-w-md">
        {description}
      </p>

      <div className="flex flex-wrap items-center justify-center gap-3 mt-6">
        {onAction && (
          <button
            onClick={onAction}
            className="px-5 py-2.5 rounded-xl bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-white text-xs font-bold shadow-lg shadow-cyan-950/60 flex items-center gap-2 transition transform active:scale-95"
          >
            <PlusCircle className="w-4 h-4" />
            {actionLabel}
          </button>
        )}
        {secondaryAction}
      </div>
    </div>
  );
}
