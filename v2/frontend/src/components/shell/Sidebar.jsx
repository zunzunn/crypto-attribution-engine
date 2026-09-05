import React from 'react';
import {
  LayoutDashboard,
  PlusCircle,
  Network,
  History,
  Database,
  FileText,
  Info,
  Settings,
  ChevronRight,
  ChevronLeft,
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
    { id: 'settings', label: 'Settings', icon: Settings },
  ];

  return (
    <aside
      className={`fixed top-0 left-0 z-40 h-screen flex flex-col justify-between transition-all duration-300 ${
        collapsed ? 'w-16' : 'w-64'
      } bg-slate-950/95 backdrop-blur-md border-r border-slate-900/50`}
    >
      <div>
        {/* Brand Header */}
        <div className={`h-14 flex items-center ${collapsed ? 'justify-center px-2' : 'justify-between px-4'} border-b border-slate-900/40`}>
          <div className="flex items-center gap-2.5 truncate">
            <div className="w-8 h-8 rounded-lg bg-slate-900 border border-slate-800 flex items-center justify-center shadow-sm flex-shrink-0">
              <Shield className="w-4 h-4 text-blue-400" />
            </div>
            {!collapsed && (
              <div className="truncate">
                <span className="text-sm font-semibold text-slate-200 block leading-tight">Attribution Engine</span>
                <span className="text-[10px] font-mono text-slate-500 block leading-tight">v2.0 Forensics</span>
              </div>
            )}
          </div>
          <button
            onClick={() => setCollapsed(!collapsed)}
            className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-900 border border-slate-800/80 transition flex items-center flex-shrink-0"
            title={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
          >
            {collapsed ? <ChevronRight className="w-4 h-4" /> : <ChevronLeft className="w-4 h-4" />}
          </button>
        </div>

        {/* Active Target Banner (compact) */}
        {activeCase && !collapsed && (
          <div className="mx-3 mt-3 p-2 rounded-lg bg-slate-900/60 border border-slate-800/50 flex items-center justify-between">
            <div className="truncate mr-2">
              <span className="text-[9px] font-mono uppercase tracking-wider text-slate-400 block">Current Target</span>
              <span className="text-xs font-mono text-slate-200 font-bold truncate block" title={activeCase.target_address}>
                {shortenAddress(activeCase.target_address, 8, 6)}
              </span>
            </div>
            <button
              onClick={() => setCurrentTab('workspace')}
              className="px-2 py-1 rounded bg-slate-800 text-slate-300 hover:text-white hover:bg-slate-700 transition text-[11px] font-medium"
              title="Open Workspace"
            >
              Open
            </button>
          </div>
        )}

        {/* Nav Items */}
        <nav className="p-2 space-y-0.5 mt-2">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = currentTab === item.id;

            if (item.id === 'new') {
              return (
                <button
                  key={item.id}
                  onClick={onNewInvestigation}
                  className={`w-full flex items-center gap-2.5 rounded-lg px-3 py-2 text-xs font-medium transition ${
                    collapsed ? 'justify-center' : ''
                  } bg-blue-600/15 hover:bg-blue-600/25 text-blue-400 hover:text-blue-300 border border-blue-500/25`}
                  title={collapsed ? item.label : undefined}
                >
                  <Icon className="w-4 h-4 text-blue-400 flex-shrink-0" />
                  {!collapsed && (
                    <span className="font-semibold tracking-wide">New Investigation</span>
                  )}
                </button>
              );
            }

            return (
              <button
                key={item.id}
                onClick={() => setCurrentTab(item.id)}
                className={`w-full flex items-center gap-2.5 rounded-lg px-3 py-2 text-xs font-medium transition ${
                  collapsed ? 'justify-center' : 'justify-between'
                } ${
                  isActive
                    ? 'bg-slate-800/80 text-white font-semibold border border-slate-700/50 shadow-sm'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900/50'
                }`}
                title={collapsed ? item.label : undefined}
              >
                <div className="flex items-center gap-2.5 truncate">
                  <Icon
                    className={`w-4 h-4 flex-shrink-0 transition ${
                      isActive ? 'text-blue-400' : 'text-slate-500'
                    }`}
                  />
                  {!collapsed && <span className="truncate">{item.label}</span>}
                </div>

                {!collapsed && item.badge && (
                  <span className="text-[8px] font-mono font-bold px-1.5 py-0.5 rounded bg-blue-950/60 text-blue-400 border border-blue-800/40">
                    {item.badge}
                  </span>
                )}
              </button>
            );
          })}
        </nav>
      </div>

      {/* Backend Connection Status at bottom */}
      <div className="p-3 border-t border-slate-900/50 bg-slate-950/80">
        {!collapsed ? (
          <div className="space-y-1">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className={`w-2 h-2 rounded-full ${apiLive ? 'bg-emerald-400 animate-pulse' : 'bg-amber-400'}`} />
                <span className="text-[11px] font-semibold text-slate-300">
                  {apiLive ? 'API ONLINE' : 'LOCAL ENGINE'}
                </span>
              </div>
              {apiLatency !== null && (
                <span className="text-[10px] font-mono text-slate-500">{apiLatency}ms</span>
              )}
            </div>
            <div className="text-[10px] font-mono text-slate-500 flex items-center gap-1">
              <Server className="w-3 h-3 text-slate-600 flex-shrink-0" />
              <span>127.0.0.1:8000</span>
            </div>
          </div>
        ) : (
          <div className="flex justify-center" title={apiLive ? 'API ONLINE' : 'LOCAL ENGINE'}>
            <span className={`w-2 h-2 rounded-full ${apiLive ? 'bg-emerald-400' : 'bg-amber-400'}`} />
          </div>
        )}
      </div>
    </aside>
  );
}