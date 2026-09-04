import React from 'react';
import {
  Search,
  Filter,
  CheckSquare,
  Square,
  X
} from 'lucide-react';
import EntityBadge from '../common/EntityBadge';
import RiskBadge from '../common/RiskBadge';

export default function FilterPanel({
  searchTerm,
  setSearchTerm,
  selectedEntities,
  setSelectedEntities,
  selectedRisks,
  setSelectedRisks,
  selectedHops,
  setSelectedHops,
  selectedAssets,
  setSelectedAssets,
  onResetFilters,
  onClose
}) {
  const entityOptions = ['VASP', 'MIXER', 'BRIDGE', 'SCAM', 'UNKNOWN'];
  const riskOptions = ['Critical', 'High', 'Medium', 'Low'];
  const hopOptions = [0, 1, 2, 3];
  const assetOptions = ['ETH', 'ERC20', 'Internal ETH'];

  const toggleEntity = (val) => {
    if (selectedEntities.includes(val)) {
      setSelectedEntities(selectedEntities.filter((item) => item !== val));
    } else {
      setSelectedEntities([...selectedEntities, val]);
    }
  };

  const toggleRisk = (val) => {
    if (selectedRisks.includes(val)) {
      setSelectedRisks(selectedRisks.filter((item) => item !== val));
    } else {
      setSelectedRisks([...selectedRisks, val]);
    }
  };

  const toggleHop = (val) => {
    if (selectedHops.includes(val)) {
      setSelectedHops(selectedHops.filter((item) => item !== val));
    } else {
      setSelectedHops([...selectedHops, val]);
    }
  };

  const toggleAsset = (val) => {
    if (selectedAssets.includes(val)) {
      setSelectedAssets(selectedAssets.filter((item) => item !== val));
    } else {
      setSelectedAssets([...selectedAssets, val]);
    }
  };

  const hasActiveFilters =
    searchTerm ||
    selectedEntities.length < entityOptions.length ||
    selectedRisks.length < riskOptions.length ||
    selectedHops.length < hopOptions.length ||
    selectedAssets.length < assetOptions.length;

  return (
    <div className="cyber-panel rounded-xl p-4 border border-slate-800/80 flex flex-col gap-4 text-xs h-full overflow-y-auto">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-slate-800/80 pb-3">
        <div className="flex items-center gap-2">
          <Filter className="w-4 h-4 text-cyan-400" />
          <h4 className="font-bold text-white uppercase text-[11px] tracking-wider">Graph Filters</h4>
        </div>
        <div className="flex items-center gap-2">
          {hasActiveFilters && (
            <button
              onClick={onResetFilters}
              className="text-[10px] text-slate-400 hover:text-cyan-300 transition underline"
            >
              Reset All
            </button>
          )}
          {onClose && (
            <button onClick={onClose} className="text-slate-500 hover:text-white p-1">
              <X className="w-3.5 h-3.5" />
            </button>
          )}
        </div>
      </div>

      {/* Address Search in Graph */}
      <div className="space-y-1.5">
        <label className="text-[10px] font-mono text-slate-400 font-bold uppercase tracking-wider block">
          Search Node Address / Tag
        </label>
        <div className="relative">
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Filter 0x... or entity"
            className="w-full pl-8 pr-3 py-1.5 text-xs font-mono rounded-lg bg-slate-950 border border-slate-700/80 text-white placeholder-slate-500 focus:outline-none focus:border-cyan-500/80"
          />
          <Search className="w-3.5 h-3.5 text-slate-500 absolute left-2.5 top-2" />
        </div>
      </div>

      {/* Entity Classification Filter */}
      <div className="space-y-2">
        <label className="text-[10px] font-mono text-slate-400 font-bold uppercase tracking-wider block">
          Entity Types
        </label>
        <div className="grid grid-cols-1 gap-1.5">
          {entityOptions.map((ent) => {
            const isChecked = selectedEntities.includes(ent);
            return (
              <button
                key={ent}
                onClick={() => toggleEntity(ent)}
                className={`w-full flex items-center justify-between p-1.5 rounded-lg border transition text-left ${
                  isChecked
                    ? 'bg-slate-800/80 border-slate-700 text-white'
                    : 'bg-slate-900/40 border-slate-800/60 text-slate-500 opacity-60'
                }`}
              >
                <div className="flex items-center gap-2">
                  {isChecked ? (
                    <CheckSquare className="w-3.5 h-3.5 text-cyan-400" />
                  ) : (
                    <Square className="w-3.5 h-3.5 text-slate-600" />
                  )}
                  <span className="font-mono text-[11px]">{ent}</span>
                </div>
                <EntityBadge type={ent} size="xs" showIcon={false} />
              </button>
            );
          })}
        </div>
      </div>

      {/* Risk Severity Filter */}
      <div className="space-y-2">
        <label className="text-[10px] font-mono text-slate-400 font-bold uppercase tracking-wider block">
          Risk Levels
        </label>
        <div className="grid grid-cols-2 gap-1.5">
          {riskOptions.map((lvl) => {
            const isChecked = selectedRisks.includes(lvl);
            return (
              <button
                key={lvl}
                onClick={() => toggleRisk(lvl)}
                className={`flex items-center justify-between p-1.5 rounded-lg border transition ${
                  isChecked
                    ? 'bg-slate-800/80 border-slate-700 text-white'
                    : 'bg-slate-900/40 border-slate-800/60 text-slate-500 opacity-60'
                }`}
              >
                <span className="font-mono text-[11px]">{lvl}</span>
                <RiskBadge level={lvl} size="xs" showIcon={false} />
              </button>
            );
          })}
        </div>
      </div>

      {/* Hop Distance Filter */}
      <div className="space-y-2">
        <label className="text-[10px] font-mono text-slate-400 font-bold uppercase tracking-wider block">
          Trace Distance (Hops)
        </label>
        <div className="flex items-center gap-1.5">
          {hopOptions.map((hop) => {
            const isChecked = selectedHops.includes(hop);
            return (
              <button
                key={hop}
                onClick={() => toggleHop(hop)}
                className={`flex-1 py-1 px-2 rounded-lg font-mono text-[11px] font-bold border transition text-center ${
                  isChecked
                    ? 'bg-cyan-500/20 text-cyan-300 border-cyan-500/40 shadow-sm'
                    : 'bg-slate-900/50 text-slate-500 border-slate-800'
                }`}
              >
                {hop === 0 ? 'Target' : `Hop ${hop}`}
              </button>
            );
          })}
        </div>
      </div>

      {/* Asset Type Filter */}
      <div className="space-y-2">
        <label className="text-[10px] font-mono text-slate-400 font-bold uppercase tracking-wider block">
          Asset Type
        </label>
        <div className="flex flex-wrap gap-1.5">
          {assetOptions.map((asset) => {
            const isChecked = selectedAssets.includes(asset);
            return (
              <button
                key={asset}
                onClick={() => toggleAsset(asset)}
                className={`py-1 px-2 rounded-lg font-mono text-[10px] font-bold border transition ${
                  isChecked
                    ? 'bg-slate-800 text-cyan-300 border-slate-700'
                    : 'bg-slate-900/40 text-slate-500 border-slate-800'
                }`}
              >
                {asset}
              </button>
            );
          })}
        </div>
      </div>

      {/* Graph Visual Legend */}
      <div className="mt-auto pt-3 border-t border-slate-800/80 space-y-2">
        <span className="text-[10px] font-mono text-slate-400 font-bold uppercase tracking-wider block">
          Node Hierarchy Legend
        </span>
        <div className="space-y-1.5 text-[11px] text-slate-400 font-mono">
          <div className="flex items-center gap-2">
            <span className="w-3 h-3 rounded-full bg-cyan-400 ring-2 ring-cyan-300" />
            <span className="text-white font-bold">Investigation Target (Root)</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="w-2.5 h-2.5 rounded-full bg-red-500" />
            <span>Mixer / High Risk Endpoint</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="w-2.5 h-2.5 rounded-full bg-blue-500" />
            <span>Exchange / VASP Deposit</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="w-2.5 h-2.5 rounded-full bg-amber-500" />
            <span>Bridge / Protocol Endpoint</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="w-2.5 h-2.5 rounded-full bg-slate-600" />
            <span>Unattributed Wallet Node</span>
          </div>
        </div>
      </div>
    </div>
  );
}
