import React from 'react';
import {
  ZoomIn,
  ZoomOut,
  Maximize2,
  RotateCcw,
  Eye,
  EyeOff,
  Search,
  HelpCircle,
  Filter
} from 'lucide-react';

export default function GraphToolbar({
  onZoomIn,
  onZoomOut,
  onFitTarget,
  onResetLayout,
  showEdgeLabels,
  setShowEdgeLabels,
  onToggleSearch,
  showSearch,
  onToggleLegend,
  showLegend,
  onToggleFilters,
  showFilters
}) {
  return (
    <div className="absolute top-4 right-4 flex flex-col gap-1.5 z-20">
      {/* Search Node */}
      {onToggleSearch && (
        <button
          onClick={onToggleSearch}
          title="Search Wallet in Graph"
          className={`p-2 rounded-xl border shadow-xl backdrop-blur-md transition ${
            showSearch
              ? 'bg-cyan-500/25 text-cyan-300 border-cyan-500/50'
              : 'bg-slate-900/90 text-slate-300 hover:text-cyan-300 hover:bg-slate-800 border-slate-700/80'
          }`}
        >
          <Search className="w-4 h-4" />
        </button>
      )}

      {/* Fit to View */}
      <button
        onClick={onFitTarget}
        title="Fit Full Graph to View"
        className="p-2 rounded-xl bg-slate-900/90 text-slate-300 hover:text-cyan-300 hover:bg-slate-800 border border-slate-700/80 shadow-xl backdrop-blur-md transition"
      >
        <Maximize2 className="w-4 h-4" />
      </button>

      {/* Zoom Controls */}
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

      {/* Re-layout */}
      <button
        onClick={onResetLayout}
        title="Reset & Re-align Layered Layout"
        className="p-2 rounded-xl bg-slate-900/90 text-slate-300 hover:text-cyan-300 hover:bg-slate-800 border border-slate-700/80 shadow-xl backdrop-blur-md transition"
      >
        <RotateCcw className="w-4 h-4" />
      </button>

      {/* Edge Amounts */}
      {setShowEdgeLabels && (
        <button
          onClick={() => setShowEdgeLabels(!showEdgeLabels)}
          title={showEdgeLabels ? 'Hide transfer amount labels' : 'Show transfer amount labels on edges'}
          className={`p-2 rounded-xl border shadow-xl backdrop-blur-md transition ${
            showEdgeLabels
              ? 'bg-cyan-500/25 text-cyan-300 border-cyan-500/50'
              : 'bg-slate-900/90 text-slate-400 hover:text-white border-slate-700/80'
          }`}
        >
          {showEdgeLabels ? <Eye className="w-4 h-4" /> : <EyeOff className="w-4 h-4" />}
        </button>
      )}

      {/* Filter toggle */}
      {onToggleFilters && (
        <button
          onClick={onToggleFilters}
          title="Toggle Graph Filters"
          className={`p-2 rounded-xl border shadow-xl backdrop-blur-md transition ${
            showFilters
              ? 'bg-cyan-500/25 text-cyan-300 border-cyan-500/50'
              : 'bg-slate-900/90 text-slate-400 hover:text-white border-slate-700/80'
          }`}
        >
          <Filter className="w-4 h-4" />
        </button>
      )}

      {/* Forensic Legend */}
      {onToggleLegend && (
        <button
          onClick={onToggleLegend}
          title="Forensic Classification Legend"
          className={`p-2 rounded-xl border shadow-xl backdrop-blur-md transition ${
            showLegend
              ? 'bg-cyan-500/25 text-cyan-300 border-cyan-500/50'
              : 'bg-slate-900/90 text-slate-400 hover:text-white border-slate-700/80'
          }`}
        >
          <HelpCircle className="w-4 h-4" />
        </button>
      )}
    </div>
  );
}
