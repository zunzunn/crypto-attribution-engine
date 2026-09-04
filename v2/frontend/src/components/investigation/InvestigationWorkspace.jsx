import React, { useState } from 'react';
import InvestigationHeader from './InvestigationHeader';
import FilterPanel from './FilterPanel';
import AddressDrawer from './AddressDrawer';
import BehavioralPanel from './BehavioralPanel';
import CytoscapeGraph from '../CytoscapeGraph';
import ForceGraph3DComponent from '../ForceGraph3D';
import EmptyState from '../common/EmptyState';

export default function InvestigationWorkspace({
  traceData,
  isLive,
  targetAddress,
  caseId,
  onAddressChange,
  onReTrace,
  onExportReport,
  onNewInvestigation
}) {
  const [viewMode, setViewMode] = useState('2D'); // '2D' or '3D'
  const [selectedNode, setSelectedNode] = useState(null);
  const [showFilters, setShowFilters] = useState(false);

  // Filters State
  const [filterSearch, setFilterSearch] = useState('');
  const [selectedEntities, setSelectedEntities] = useState(['VASP', 'MIXER', 'BRIDGE', 'SCAM', 'UNKNOWN']);
  const [selectedRisks, setSelectedRisks] = useState(['Critical', 'High', 'Medium', 'Low']);
  const [selectedHops, setSelectedHops] = useState([0, 1, 2, 3]);
  const [selectedAssets, setSelectedAssets] = useState(['ETH', 'ERC20', 'Internal ETH']);

  const handleResetFilters = () => {
    setFilterSearch('');
    setSelectedEntities(['VASP', 'MIXER', 'BRIDGE', 'SCAM', 'UNKNOWN']);
    setSelectedRisks(['Critical', 'High', 'Medium', 'Low']);
    setSelectedHops([0, 1, 2, 3]);
    setSelectedAssets(['ETH', 'ERC20', 'Internal ETH']);
  };

  if (!traceData) {
    return (
      <div className="py-8">
        <EmptyState
          title="No Active Investigation In Workspace"
          description="Start a forensic trace on an Ethereum wallet address or select a prior investigation from the case manager to inspect its interactive transaction graph."
          actionLabel="Start New Investigation"
          onAction={onNewInvestigation}
        />
      </div>
    );
  }

  const traceResults = traceData.trace_results || {};
  const discovered = traceResults.discovered_addresses || [];
  const patterns = traceData.patterns || {};
  const overallRisk = traceResults.overall_risk || {};
  const liveStats = traceData.live_data_stats || null;

  // Real summary stats
  const totalAddresses = discovered.length;
  const highRiskCount = discovered.filter(
    (n) => n?.risk?.risk_level === 'Critical' || n?.risk?.risk_level === 'High'
  ).length;
  const attributedCount = discovered.filter(
    (n) => n?.entity && n?.entity !== 'Unknown' && n?.entity_type !== 'Unknown'
  ).length;
  const patternCount = patterns.summary?.total_patterns_detected || 0;

  // Calculate total transactions analyzed from graph
  let totalTxs = 0;
  Object.values(traceData.graph || {}).forEach((txList) => {
    totalTxs += (txList || []).length;
  });

  const handleSelectAddressFromBehavioral = (addr) => {
    const found = discovered.find(
      (n) => (n.address || '').toLowerCase() === (addr || '').toLowerCase()
    );
    if (found) {
      setSelectedNode(found);
    } else {
      setSelectedNode({
        address: addr,
        entity: 'Unknown',
        entity_type: 'Unknown',
        confidence: 0,
        risk: { score: 0, risk_level: 'Low', reasons: [] }
      });
    }
  };

  return (
    <div className="space-y-4">
      {/* 1. Case Header */}
      <InvestigationHeader
        targetAddress={traceData.target_address || targetAddress}
        caseId={caseId || 'CASE-2026-LIVE'}
        overallRisk={overallRisk}
        isLive={Boolean(traceData.live_data !== undefined ? traceData.live_data : isLive)}
        liveStats={liveStats}
        maxHops={traceData.max_hops || 2}
        viewMode={viewMode}
        setViewMode={setViewMode}
        showFilters={showFilters}
        setShowFilters={setShowFilters}
        onReTrace={onReTrace}
        onExportReport={onExportReport}
      />

      {/* 2. Compact Intelligence Summary Bar */}
      <div className="cyber-panel p-3 rounded-xl border border-slate-800/80 grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3 text-xs">
        <div className="border-r border-slate-800/60 pr-2">
          <span className="text-[10px] font-mono text-slate-400 uppercase tracking-wider block">Addresses</span>
          <span className="font-mono text-white font-bold text-sm">{totalAddresses}</span>
          <span className="text-[10px] text-slate-500 block">Nodes in graph</span>
        </div>

        <div className="border-r border-slate-800/60 pr-2">
          <span className="text-[10px] font-mono text-slate-400 uppercase tracking-wider block">Transactions</span>
          <span className="font-mono text-white font-bold text-sm">{totalTxs}</span>
          <span className="text-[10px] text-slate-500 block">Edges mapped</span>
        </div>

        <div className="border-r border-slate-800/60 pr-2">
          <span className="text-[10px] font-mono text-slate-400 uppercase tracking-wider block">Max Hops</span>
          <span className="font-mono text-cyan-400 font-bold text-sm">{traceData.max_hops || 2} Hops</span>
          <span className="text-[10px] text-slate-500 block">BFS depth</span>
        </div>

        <div className="border-r border-slate-800/60 pr-2">
          <span className="text-[10px] font-mono text-slate-400 uppercase tracking-wider block">High / Critical</span>
          <span className="font-mono text-red-400 font-bold text-sm">{highRiskCount}</span>
          <span className="text-[10px] text-slate-500 block">Threat entities</span>
        </div>

        <div className="border-r border-slate-800/60 pr-2">
          <span className="text-[10px] font-mono text-slate-400 uppercase tracking-wider block">Attributed</span>
          <span className="font-mono text-blue-400 font-bold text-sm">{attributedCount}</span>
          <span className="text-[10px] text-slate-500 block">Known registries</span>
        </div>

        <div>
          <span className="text-[10px] font-mono text-slate-400 uppercase tracking-wider block">Anomalies</span>
          <span className="font-mono text-amber-400 font-bold text-sm">{patternCount}</span>
          <span className="text-[10px] text-slate-500 block">Heuristics active</span>
        </div>
      </div>

      {/* 3. Main Split Canvas: [Filters] [Graph Canvas] [Address Drawer] */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-4 h-[660px] min-h-[580px]">
        {/* Optional Collapsible Filter Panel */}
        {showFilters && (
          <div className="lg:col-span-3 h-full animate-fade-in">
            <FilterPanel
              searchTerm={filterSearch}
              setSearchTerm={setFilterSearch}
              selectedEntities={selectedEntities}
              setSelectedEntities={setSelectedEntities}
              selectedRisks={selectedRisks}
              setSelectedRisks={setSelectedRisks}
              selectedHops={selectedHops}
              setSelectedHops={setSelectedHops}
              selectedAssets={selectedAssets}
              setSelectedAssets={setSelectedAssets}
              onResetFilters={handleResetFilters}
              onClose={() => setShowFilters(false)}
            />
          </div>
        )}

        {/* Center Hero Graph Canvas (70-75% width when filters closed) */}
        <div
          className={`h-full transition-all duration-300 ${
            showFilters ? 'lg:col-span-5' : 'lg:col-span-8 xl:col-span-9'
          }`}
        >
          {viewMode === '2D' ? (
            <CytoscapeGraph
              traceData={traceData}
              selectedNode={selectedNode}
              onSelectNode={(node) => setSelectedNode(node)}
              filterSearch={filterSearch}
              selectedEntities={selectedEntities}
              selectedRisks={selectedRisks}
              selectedHops={selectedHops}
            />
          ) : (
            <ForceGraph3DComponent
              traceData={traceData}
              selectedNode={selectedNode}
              onSelectNode={(node) => setSelectedNode(node)}
            />
          )}
        </div>

        {/* Right Address Intelligence Drawer (25-30% width) - Always Visible */}
        <div
          className={`h-full transition-all duration-300 ${
            showFilters ? 'lg:col-span-4' : 'lg:col-span-4 xl:col-span-3'
          }`}
        >
          <AddressDrawer
            selectedNode={selectedNode}
            graphData={traceData.graph}
            onClose={() => setSelectedNode(null)}
            onFocusNode={() => {
              // Node is automatically selected & focused via selectedNode prop
            }}
            onTraceAsNewTarget={(addr) => {
              if (onAddressChange) onAddressChange(addr);
            }}
          />
        </div>
      </div>

      {/* 4. Dedicated Behavioral Intelligence Findings Section */}
      <BehavioralPanel
        patterns={patterns}
        onSelectAddress={handleSelectAddressFromBehavioral}
      />
    </div>
  );
}
