import React from 'react';
import {
  ZoomIn,
  ZoomOut,
  Crosshair,
  RefreshCw,
  Eye,
  EyeOff
} from 'lucide-react';

export default function GraphToolbar({
  onZoomIn,
  onZoomOut,
  onFitTarget,
  onResetLayout,
  showEdgeLabels,
  setShowEdgeLabels
}) {
  return (
    <div className="absolute top-4 right-4 flex flex-col gap-1.5 z-20">
      <button
        onClick={onZoomIn}
        title="Zoom In (+)"
        className="p-2 rounded-xl bg-slate-900/90 text-slate-300 hover:text-cyan-300 hover:bg-slate-800 border border-slate-700/80 shadow-xl backdrop-blur-md transition"
      >
        <ZoomIn className="w-4 h-4" />
      </button>

      <button
        onClick={onZoomOut}
        title="Zoom Out (-)"
        className="p-2 rounded-xl bg-slate-900/90 text-slate-300 hover:text-cyan-300 hover:bg-slate-800 border border-slate-700/80 shadow-xl backdrop-blur-md transition"
      >
        <ZoomOut className="w-4 h-4" />
      </button>

      <button
        onClick={onFitTarget}
        title="Centre on Target Wallet"
        className="p-2 rounded-xl bg-slate-900/90 text-slate-300 hover:text-cyan-300 hover:bg-slate-800 border border-slate-700/80 shadow-xl backdrop-blur-md transition"
      >
        <Crosshair className="w-4 h-4" />
      </button>

      <button
        onClick={onResetLayout}
        title="Re-layout & Auto Arrange"
        className="p-2 rounded-xl bg-slate-900/90 text-slate-300 hover:text-cyan-300 hover:bg-slate-800 border border-slate-700/80 shadow-xl backdrop-blur-md transition"
      >
        <RefreshCw className="w-4 h-4" />
      </button>

      {setShowEdgeLabels && (
        <button
          onClick={() => setShowEdgeLabels(!showEdgeLabels)}
          title={showEdgeLabels ? 'Hide all edge amounts' : 'Show all edge amounts'}
          className={`p-2 rounded-xl border shadow-xl backdrop-blur-md transition ${
            showEdgeLabels
              ? 'bg-cyan-500/20 text-cyan-300 border-cyan-500/40'
              : 'bg-slate-900/90 text-slate-400 hover:text-white border-slate-700/80'
          }`}
        >
          {showEdgeLabels ? <Eye className="w-4 h-4" /> : <EyeOff className="w-4 h-4" />}
        </button>
      )}
    </div>
  );
}
