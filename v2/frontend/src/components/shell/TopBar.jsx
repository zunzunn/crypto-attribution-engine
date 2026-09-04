import React, { useState } from 'react';
import {
  Search,
  Bell,
  Radio,
  UserCheck,
  Copy,
  Check,
  ExternalLink,
  CheckCircle,
  AlertCircle
} from 'lucide-react';
import { shortenAddress } from '../../utils/formatters';
import RiskBadge from '../common/RiskBadge';

export default function TopBar({
  activeCase,
  isLive,
  onSearch,
  _onNewInvestigation,
  collapsed
}) {
  const [searchInput, setSearchInput] = useState('');
  const [copied, setCopied] = useState(false);
  const [showNotifications, setShowNotifications] = useState(false);

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    if (searchInput.trim()) {
      onSearch(searchInput.trim());
      setSearchInput('');
    }
  };

  const handleCopyTarget = () => {
    if (activeCase?.target_address) {
      navigator.clipboard.writeText(activeCase.target_address);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  return (
    <header
      className={`sticky top-0 z-30 h-16 bg-[#070b14]/90 backdrop-blur-md border-b border-slate-800/80 px-4 sm:px-6 flex items-center justify-between gap-4 transition-all duration-300 ${
        collapsed ? 'ml-16' : 'ml-64'
      }`}
    >
      {/* Left: Current Investigation / Case Status */}
      <div className="flex items-center gap-3 min-w-0">
        {activeCase ? (
          <div className="flex items-center gap-2.5 truncate">
            <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700">
              {activeCase.case_id || 'ACTIVE CASE'}
            </span>
            <div className="flex items-center gap-1.5 font-mono text-xs text-white truncate">
              <span className="truncate hidden sm:inline" title={activeCase.target_address}>
                {shortenAddress(activeCase.target_address, 10, 8)}
              </span>
              <span className="sm:hidden truncate">
                {shortenAddress(activeCase.target_address, 6, 4)}
              </span>
              <button
                onClick={handleCopyTarget}
                className="p-1 rounded hover:bg-slate-800 text-slate-400 hover:text-cyan-300 transition"
                title="Copy Target Address"
              >
                {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
              </button>
              <a
                href={`https://etherscan.io/address/${activeCase.target_address}`}
                target="_blank"
                rel="noreferrer"
                className="p-1 rounded hover:bg-slate-800 text-slate-400 hover:text-cyan-300 transition"
                title="View on Etherscan"
              >
                <ExternalLink className="w-3.5 h-3.5" />
              </a>
            </div>
            {activeCase.risk_level && (
              <div className="hidden md:inline-block">
                <RiskBadge level={activeCase.risk_level} score={activeCase.risk_score} size="xs" />
              </div>
            )}
          </div>
        ) : (
          <div className="flex items-center gap-2 text-xs text-slate-400">
            <span className="w-2 h-2 rounded-full bg-slate-500" />
            <span className="font-medium">No Active Case Selected</span>
          </div>
        )}
      </div>

      {/* Center: Global Address Search */}
      <form onSubmit={handleSearchSubmit} className="relative flex-1 max-w-md hidden md:block">
        <input
          type="text"
          value={searchInput}
          onChange={(e) => setSearchInput(e.target.value)}
          placeholder="Search Ethereum wallet address (0x...) or Case ID..."
          className="w-full pl-9 pr-4 py-1.5 text-xs font-mono rounded-xl bg-slate-900/90 border border-slate-700/80 text-white placeholder-slate-500 focus:outline-none focus:border-cyan-500/80 focus:ring-1 focus:ring-cyan-500/40 transition"
        />
        <Search className="w-4 h-4 text-slate-500 absolute left-3 top-2.5" />
      </form>

      {/* Right Controls: Live/Local status, notifications, investigator profile */}
      <div className="flex items-center gap-3">
        {/* Live / Local Indicator */}
        <div
          className={`flex items-center gap-1.5 px-2.5 py-1 rounded-lg border text-xs font-mono ${
            isLive
              ? 'bg-cyan-500/10 text-cyan-300 border-cyan-500/30'
              : 'bg-slate-850 text-slate-400 border-slate-700/60'
          }`}
        >
          <Radio className={`w-3 h-3 ${isLive ? 'text-cyan-400 animate-pulse' : 'text-slate-500'}`} />
          <span className="hidden sm:inline">{isLive ? 'ETH MAINNET LIVE' : 'LOCAL CACHED'}</span>
        </div>

        {/* Notifications Popover */}
        <div className="relative">
          <button
            onClick={() => setShowNotifications(!showNotifications)}
            className="p-2 rounded-xl text-slate-400 hover:text-white hover:bg-slate-800/80 border border-slate-850 transition relative"
            title="System Notifications"
          >
            <Bell className="w-4 h-4" />
            <span className="absolute top-1.5 right-1.5 w-2 h-2 rounded-full bg-cyan-400" />
          </button>

          {showNotifications && (
            <div className="absolute right-0 mt-2 w-72 cyber-panel rounded-xl border border-slate-700/80 shadow-2xl p-3 z-50 text-xs">
              <div className="flex items-center justify-between border-b border-slate-800 pb-2 mb-2">
                <span className="font-bold text-white uppercase text-[10px] tracking-wider">System Feed</span>
                <span className="text-[10px] text-cyan-400 font-mono">Realtime</span>
              </div>
              <div className="space-y-2">
                <div className="flex items-start gap-2 text-slate-300">
                  <CheckCircle className="w-3.5 h-3.5 text-emerald-400 mt-0.5 flex-shrink-0" />
                  <div>
                    <p className="font-medium">Backend Service Ready</p>
                    <p className="text-[10px] text-slate-400">FastAPI attribution engine running on port 8000</p>
                  </div>
                </div>
                <div className="flex items-start gap-2 text-slate-300">
                  <AlertCircle className="w-3.5 h-3.5 text-cyan-400 mt-0.5 flex-shrink-0" />
                  <div>
                    <p className="font-medium">Registry Synchronized</p>
                    <p className="text-[10px] text-slate-400">VASPs, bridges, and mixer signatures loaded</p>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Investigator Placeholder */}
        <div className="flex items-center gap-2 pl-2 border-l border-slate-800">
          <div className="w-8 h-8 rounded-xl bg-slate-800 border border-slate-700 text-cyan-400 flex items-center justify-center font-bold text-xs">
            <UserCheck className="w-4 h-4" />
          </div>
          <div className="hidden lg:block text-left">
            <span className="text-xs font-semibold text-white block leading-tight">INV-7409</span>
            <span className="text-[10px] text-slate-400 block leading-tight">Lead Analyst</span>
          </div>
        </div>
      </div>
    </header>
  );
}
