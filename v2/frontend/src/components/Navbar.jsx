import React from 'react';
import { Shield, Search, Cpu, Activity, BarChart3, GitFork, FileText, Database } from 'lucide-react';

export default function Navbar({ currentTab, setCurrentTab, apiLive, onQuickSearch }) {
  const [searchInput, setSearchInput] = React.useState('');

  const handleSearch = (e) => {
    e.preventDefault();
    if (searchInput.trim()) {
      onQuickSearch(searchInput.trim());
    }
  };

  return (
    <header className="glass-panel sticky top-0 z-40 border-b border-slate-800/80 px-4 py-3">
      <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-center justify-between gap-4">
        
        {/* Brand Title */}
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-xl bg-gradient-to-br from-cyan-500/20 to-blue-600/30 border border-cyan-500/40 text-cyan-400 shadow-lg shadow-cyan-950/50">
            <Shield className="w-6 h-6" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="font-bold text-lg text-white tracking-wide">Crypto Attribution Engine</h1>
              <span className="px-2 py-0.5 text-xs font-semibold rounded-md bg-cyan-950 text-cyan-400 border border-cyan-800/50">
                v2.0
              </span>
            </div>
            <p className="text-xs text-slate-400">Forensic Blockchain Tracing & Threat Attribution</p>
          </div>
        </div>

        {/* Quick Address Search */}
        <form onSubmit={handleSearch} className="relative w-full md:w-96">
          <input
            type="text"
            placeholder="Search Ethereum wallet address (0x...)"
            value={searchInput}
            onChange={(e) => setSearchInput(e.target.value)}
            className="w-full pl-9 pr-4 py-1.5 text-xs rounded-lg bg-slate-900/90 border border-slate-700/60 text-slate-200 placeholder-slate-500 focus:outline-none focus:border-cyan-500/80 focus:ring-1 focus:ring-cyan-500/50 font-mono transition"
          />
          <Search className="w-4 h-4 text-slate-500 absolute left-2.5 top-2" />
        </form>

        {/* Navigation Tabs & API Status */}
        <div className="flex items-center gap-3">
          <nav className="flex items-center gap-1 bg-slate-900/80 p-1 rounded-lg border border-slate-800">
            <button
              onClick={() => setCurrentTab('dashboard')}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium transition ${
                currentTab === 'dashboard'
                  ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/30 shadow-sm'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
              }`}
            >
              <BarChart3 className="w-3.5 h-3.5" />
              Dashboard
            </button>

            <button
              onClick={() => setCurrentTab('trace')}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium transition ${
                currentTab === 'trace'
                  ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/30 shadow-sm'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
              }`}
            >
              <GitFork className="w-3.5 h-3.5" />
              Trace Graph
            </button>

            <button
              onClick={() => setCurrentTab('entities')}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium transition ${
                currentTab === 'entities'
                  ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/30 shadow-sm'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
              }`}
            >
              <Database className="w-3.5 h-3.5" />
              Registry
            </button>

            <button
              onClick={() => setCurrentTab('report')}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium transition ${
                currentTab === 'report'
                  ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/30 shadow-sm'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
              }`}
            >
              <FileText className="w-3.5 h-3.5" />
              Report
            </button>
          </nav>

          {/* Live API Status Pill */}
          <div className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg bg-slate-900/90 border border-slate-800 text-xs">
            <Activity className={`w-3.5 h-3.5 ${apiLive ? 'text-emerald-400 animate-pulse' : 'text-amber-400'}`} />
            <span className="hidden sm:inline font-mono text-[11px] text-slate-300">
              {apiLive ? 'API LIVE' : 'OFFLINE MOCK'}
            </span>
          </div>
        </div>

      </div>
    </header>
  );
}
