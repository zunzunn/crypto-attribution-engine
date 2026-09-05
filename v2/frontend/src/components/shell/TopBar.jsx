import React, { useState } from 'react';
import {
  Search,
  Bell,
  ExternalLink,
  Copy,
  Check,
  UserCheck,
  Radio,
  AlertTriangle
} from 'lucide-react';
import { shortenAddress } from '../../utils/formatters';
import RiskBadge from '../common/RiskBadge';

export default function TopBar({
  activeCase,
  isLive,
  onSearch,
  onNewInvestigation,
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
      className={`sticky top-0 z-30 h-16 border-b border-border px-4 sm:px-6 flex items-center justify-between gap-4 transition-all duration-300 ${
        collapsed ? 'ml-16' : 'ml-64'
      } bg-surface/85 backdrop-blur-md`}
    >
      {/* Left: Current Investigation / Case Status */}
      <div className="flex items-center gap-2 min-w-0">
        {activeCase ? (
          <div className="flex items-center gap-2 truncate">
            <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded-lg bg-surface-subtle text-secondary border border-border">
              {activeCase.case_id || 'ACTIVE CASE'}
            </span>
            <div className="flex items-center gap-1.5 font-mono text-xs text-secondary truncate">
              <span className="truncate hidden sm:inline text-primary font-semibold" title={activeCase.target_address}>
                {shortenAddress(activeCase.target_address, 10, 8)}
              </span>
              <span className="sm:hidden truncate text-primary font-semibold">
                {shortenAddress(activeCase.target_address, 6, 4)}
              </span>
              <button
                onClick={handleCopyTarget}
                className="p-1 rounded-md hover:bg-surface-subtle text-secondary hover:text-primary transition"
                title="Copy Target Address"
              >
                {copied ? <Check className="w-3.5 h-3.5 text-emerald-500" /> : <Copy className="w-3.5 h-3.5" />}
              </button>
              <a
                href={`https://etherscan.io/address/${activeCase.target_address}`}
                target="_blank"
                rel="noreferrer"
                className="p-1 rounded-md hover:bg-surface-subtle text-secondary hover:text-primary transition"
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
          <div className="flex items-center gap-2 text-xs text-secondary">
            <span className="w-2 h-2 rounded-full bg-slate-400" />
            <span>No Active Case Selected</span>
          </div>
        )}
      </div>

      {/* Center: Global Address Search */}
      <form onSubmit={handleSearchSubmit} className="relative flex-1 max-w-sm w-full sm:w-auto">
        <input
          type="text"
          value={searchInput}
          onChange={(e) => setSearchInput(e.target.value)}
          placeholder="Search Ethereum wallet address (0x...) or Case ID..."
          className="w-full pl-9 pr-3 py-1.5 text-xs font-mono rounded-xl bg-surface border border-border text-primary placeholder-secondary/60 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition shadow-inner"
        />
        <Search className="w-3.5 h-3.5 text-secondary absolute left-3 top-2" />
      </form>

      {/* Right Controls: Live/Local status, notifications, investigator profile */}
      <div className="flex items-center gap-2">
        {/* Live / Local Indicator */}
        <div
          className={`flex items-center gap-1.5 px-2.5 py-1 rounded-lg border text-[11px] font-mono ${
            isLive
              ? 'bg-blue-500/10 text-blue-500 border-blue-500/30'
              : 'bg-surface-subtle text-secondary border-border'
          }`}
        >
          <Radio className={`w-3 h-3 ${isLive ? 'text-blue-500 animate-pulse' : 'text-secondary'}`} />
          <span className="hidden sm:inline font-semibold">{isLive ? 'ETH MAINNET' : 'LOCAL CACHED'}</span>
        </div>

        {/* Notifications Popover */}
        <div className="relative">
          <button
            onClick={() => setShowNotifications(!showNotifications)}
            className="p-2 rounded-xl text-secondary hover:text-primary hover:bg-surface-subtle border border-border transition relative"
            title="System Notifications"
          >
            <Bell className="w-3.5 h-3.5" />
            <span className="absolute top-1.5 right-1.5 w-1.5 h-1.5 rounded-full bg-blue-500" />
          </button>

          {showNotifications && (
            <div className="absolute right-0 mt-2 w-64 bg-surface rounded-xl border border-border p-3 z-50 text-xs shadow-lg">
              <div className="flex items-center justify-between border-b border-border pb-2 mb-2">
                <span className="font-bold text-primary uppercase text-[9px] tracking-wider">System Feed</span>
                <span className="text-[9px] text-blue-500 font-mono">Realtime</span>
              </div>
              <div className="space-y-2">
                <div className="flex items-start gap-2 text-secondary">
                  <Check className="w-3 h-3 text-emerald-500 mt-0.5 flex-shrink-0" />
                  <div>
                    <p className="font-medium text-primary text-xs">Backend Service Ready</p>
                    <p className="text-[10px] text-secondary">FastAPI attribution engine running</p>
                  </div>
                </div>
                <div className="flex items-start gap-2 text-secondary">
                  <AlertTriangle className="w-3 h-3 text-amber-500 mt-0.5 flex-shrink-0" />
                  <div>
                    <p className="font-medium text-primary text-xs">Registry Synchronized</p>
                    <p className="text-[10px] text-secondary">VASPs, bridges, and mixer signatures loaded</p>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Investigator Placeholder */}
        <div className="flex items-center gap-2 pl-2 border-l border-border">
          <div className="w-7 h-7 rounded-xl bg-surface-subtle border border-border flex items-center justify-center text-secondary font-bold text-xs">
            <UserCheck className="w-3.5 h-3.5" />
          </div>
          <div className="text-left hidden lg:block">
            <span className="text-xs font-semibold text-primary block leading-tight">INV-7409</span>
            <span className="text-[10px] text-secondary block leading-tight">Lead Analyst</span>
          </div>
        </div>
      </div>
    </header>
  );
}