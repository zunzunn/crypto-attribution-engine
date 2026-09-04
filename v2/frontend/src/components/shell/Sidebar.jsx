import React from 'react';
import {
  LayoutDashboard,
  PlusCircle,
  Network,
  History,
  Database,
  FileText,
  Info,
  ChevronLeft,
  ChevronRight,
  Shield,
  Server
} from 'lucide-react';
import { shortenAddress } from '../../utils/formatters';

export default function Sidebar({
  currentTab,
  setCurrentTab,
  collapsed,
  setCollapsed,
  apiLive,
  apiLatency,
  activeCase,
  onNewInvestigation
}) {
  const navItems = [
    { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
    { id: 'new', label: 'New Investigation', icon: PlusCircle, isSpecial: true },
    { id: 'workspace', label: 'Workspace', icon: Network, badge: activeCase ? 'ACTIVE' : null },
    { id: 'history', label: 'Investigations', icon: History },
    { id: 'entities', label: 'Entity Registry', icon: Database },
    { id: 'reports', label: 'Reports', icon: FileText },
    { id: 'system', label: 'System / About', icon: Info },
  ];

  return (
    <aside
      className={`fixed top-0 left-0 z-40 h-screen bg-[#070b14] border-r border-slate-800/80 transition-all duration-300 flex flex-col justify-between ${
        collapsed ? 'w-16' : 'w-64'
      }`}
    >
      {/* Brand Header */}
      <div>
        <div className="h-16 flex items-center justify-between px-4 border-b border-slate-800/80">
          {!collapsed ? (
            <div className="flex items-center gap-2.5 overflow-hidden">
              <div className="w-9 h-9 rounded-xl bg-cyan-500/15 border border-cyan-500/30 text-cyan-400 flex items-center justify-center flex-shrink-0 shadow-lg shadow-cyan-950/50">
                <Shield className="w-5 h-5" />
              </div>
              <div className="truncate">
                <div className="flex items-center gap-1.5">
                  <h1 className="font-bold text-sm tracking-wide text-white">ATTRIBUTION</h1>
                  <span className="text-[10px] font-mono px-1.5 py-0.2 rounded bg-cyan-950 text-cyan-400 border border-cyan-800/60 font-semibold">
                    v2.0
                  </span>
                </div>
                <p className="text-[10px] text-slate-400 font-mono truncate">Cyber Forensics Engine</p>
              </div>
            </div>
          ) : (
            <div className="w-9 h-9 rounded-xl bg-cyan-500/15 border border-cyan-500/30 text-cyan-400 flex items-center justify-center mx-auto shadow-lg shadow-cyan-950/50">
              <Shield className="w-5 h-5" />
            </div>
          )}

          <button
            onClick={() => setCollapsed(!collapsed)}
            className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-850 border border-transparent hover:border-slate-700 transition"
            title={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
          >
            {collapsed ? <ChevronRight className="w-4 h-4" /> : <ChevronLeft className="w-4 h-4" />}
          </button>
        </div>

        {/* Active Target Banner (if not collapsed) */}
        {!collapsed && activeCase && (
          <div className="mx-3 mt-3 p-2.5 rounded-xl bg-slate-900/90 border border-slate-800/80 flex items-center justify-between">
            <div className="truncate">
              <span className="text-[9px] font-mono uppercase tracking-wider text-slate-400 block">Current Target</span>
              <span className="text-xs font-mono text-cyan-300 font-bold truncate block" title={activeCase.target_address}>
                {shortenAddress(activeCase.target_address, 8, 6)}
              </span>
            </div>
            <button
              onClick={() => setCurrentTab('workspace')}
              className="p-1.5 rounded-lg bg-cyan-500/20 text-cyan-300 hover:bg-cyan-500/30 transition text-xs font-mono"
              title="Open Workspace"
            >
              Open
            </button>
          </div>
        )}

        {/* Nav Items */}
        <nav className="p-3 space-y-1.5 mt-2">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = currentTab === item.id;

            if (item.id === 'new') {
              return (
                <button
                  key={item.id}
                  onClick={onNewInvestigation}
                  className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-xs font-semibold transition group ${
                    collapsed ? 'justify-center' : ''
                  } bg-gradient-to-r from-cyan-500/20 to-blue-600/20 hover:from-cyan-500/30 hover:to-blue-600/30 border border-cyan-500/40 text-cyan-300 shadow-md shadow-cyan-950/40`}
                  title={collapsed ? item.label : undefined}
                >
                  <Icon className="w-4 h-4 text-cyan-400 flex-shrink-0" />
                  {!collapsed && (
                    <span className="tracking-wide">New Investigation</span>
                  )}
                </button>
              );
            }

            return (
              <button
                key={item.id}
                onClick={() => setCurrentTab(item.id)}
                className={`w-full flex items-center gap-3 px-3 py-2 rounded-xl text-xs font-medium transition ${
                  collapsed ? 'justify-center' : 'justify-between'
                } ${
                  isActive
                    ? 'bg-slate-800/90 text-white font-semibold border border-slate-700/80 shadow-sm'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900/60'
                }`}
                title={collapsed ? item.label : undefined}
              >
                <div className="flex items-center gap-3 truncate">
                  <Icon
                    className={`w-4 h-4 flex-shrink-0 transition ${
                      isActive ? 'text-cyan-400' : 'text-slate-400 group-hover:text-slate-300'
                    }`}
                  />
                  {!collapsed && <span className="truncate">{item.label}</span>}
                </div>

                {!collapsed && item.badge && (
                  <span className="text-[9px] font-mono font-bold px-1.5 py-0.5 rounded bg-cyan-950 text-cyan-400 border border-cyan-800/60">
                    {item.badge}
                  </span>
                )}
              </button>
            );
          })}
        </nav>
      </div>

      {/* Backend Connection Status at bottom */}
      <div className="p-3 border-t border-slate-800/80 bg-slate-950/70">
        {!collapsed ? (
          <div className="space-y-1.5">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className={`w-2 h-2 rounded-full ${apiLive ? 'bg-emerald-400 animate-pulse' : 'bg-amber-400'}`} />
                <span className="text-[11px] font-semibold text-slate-300">
                  {apiLive ? 'API ONLINE' : 'OFFLINE MOCK'}
                </span>
              </div>
              {apiLatency !== null && (
                <span className="text-[10px] font-mono text-slate-400">{apiLatency}ms</span>
              )}
            </div>
            <div className="text-[10px] font-mono text-slate-400 flex items-center gap-1 truncate">
              <Server className="w-3 h-3 text-slate-400 flex-shrink-0" />
              <span className="truncate">127.0.0.1:8000</span>
            </div>
          </div>
        ) : (
          <div className="flex justify-center" title={apiLive ? 'API ONLINE' : 'OFFLINE MOCK'}>
            <span className={`w-2.5 h-2.5 rounded-full ${apiLive ? 'bg-emerald-400 animate-pulse' : 'bg-amber-400'}`} />
          </div>
        )}
      </div>
    </aside>
  );
}
