import React, { useState, useEffect } from 'react';
import {
  Shield,
  Server,
  Cpu,
  Database,
  Layers,
  Zap,
  Moon,
  Sun,
  Laptop,
  Palette,
  SlidersHorizontal,
  Layout,
  Info,
  CheckCircle,
  AlertCircle,
  RefreshCw
} from 'lucide-react';

export default function SettingsView({
  theme: appTheme,
  setTheme: appSetTheme,
  onCheckHealth,
  apiLive,
  apiLatency
}) {
  const STORED_THEME_KEY = 'crypto-attribution-theme';

  const [localTheme, setLocalTheme] = useState(() => {
    return appTheme || localStorage.getItem(STORED_THEME_KEY) || 'dark';
  });

  const activeTheme = appTheme || localTheme;

  const handleThemeSelect = (newTheme) => {
    setLocalTheme(newTheme);
    localStorage.setItem(STORED_THEME_KEY, newTheme);
    document.documentElement.setAttribute('data-theme', newTheme);
    if (appSetTheme) {
      appSetTheme(newTheme);
    }
  };

  const [accentColor, setAccentColor] = useState(() => {
    return localStorage.getItem('crypto-attribution-accent') || 'blue';
  });

  const [density, setDensity] = useState(() => {
    return localStorage.getItem('crypto-attribution-density') || 'comfortable';
  });

  const [isChecking, setIsChecking] = useState(false);

  useEffect(() => {
    localStorage.setItem('crypto-attribution-accent', accentColor);
  }, [accentColor]);

  useEffect(() => {
    localStorage.setItem('crypto-attribution-density', density);
  }, [density]);

  const handleRefreshHealth = async () => {
    if (!onCheckHealth) return;
    setIsChecking(true);
    await onCheckHealth();
    setTimeout(() => setIsChecking(false), 500);
  };

  const themeOptions = [
    { value: 'light', label: 'Light', icon: Sun, desc: 'Crisp light surfaces' },
    { value: 'dark', label: 'Dark', icon: Moon, desc: 'Deep forensic contrast' },
    { value: 'system', label: 'System', icon: Laptop, desc: 'Match OS preference' },
  ];

  const accentOptions = [
    { value: 'blue', label: 'Apple Blue', hex: '#0071e3' },
    { value: 'purple', label: 'Forensic Purple', hex: '#8b5cf6' },
    { value: 'teal', label: 'Cyber Teal', hex: '#0d9488' },
    { value: 'green', label: 'Emerald Mint', hex: '#10b981' },
    { value: 'orange', label: 'Amber Orange', hex: '#f97316' },
  ];

  return (
    <div className="max-w-4xl mx-auto space-y-6 py-2">
      {/* Page Header */}
      <div className="border-b border-slate-800/50 pb-4">
        <h1 className="text-2xl font-bold text-slate-100 tracking-tight">Preferences & Settings</h1>
        <p className="text-sm text-slate-500 mt-1">
          Configure interface appearance, forensic accent palettes, and backend diagnostics.
        </p>
      </div>

      {/* 1. Appearance Section */}
      <div className="bg-slate-900/60 border border-slate-800/50 rounded-2xl p-6 backdrop-blur-md space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-base font-semibold text-slate-100">Appearance Theme</h2>
            <p className="text-xs text-slate-500 mt-0.5">Select your preferred color scheme.</p>
          </div>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          {themeOptions.map((opt) => {
            const Icon = opt.icon;
            const isSelected = activeTheme === opt.value;
            return (
              <button
                key={opt.value}
                type="button"
                onClick={() => handleThemeSelect(opt.value)}
                className={`p-4 rounded-xl border text-left transition flex flex-col justify-between gap-3 ${
                  isSelected
                    ? 'border-blue-500 bg-blue-500/10 text-white shadow-md shadow-blue-950/20'
                    : 'border-slate-800/80 bg-slate-950/40 text-slate-400 hover:border-slate-700 hover:text-slate-200'
                }`}
              >
                <div className="flex items-center justify-between">
                  <div className={`p-2 rounded-lg ${isSelected ? 'bg-blue-500 text-white' : 'bg-slate-800 text-slate-400'}`}>
                    <Icon className="w-4 h-4" />
                  </div>
                  {isSelected && (
                    <span className="w-2 h-2 rounded-full bg-blue-500" />
                  )}
                </div>
                <div>
                  <div className="font-semibold text-sm">{opt.label}</div>
                  <div className="text-[11px] text-slate-500">{opt.desc}</div>
                </div>
              </button>
            );
          })}
        </div>
      </div>

      {/* 2. Accent Palette Section */}
      <div className="bg-slate-900/60 border border-slate-800/50 rounded-2xl p-6 backdrop-blur-md space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-base font-semibold text-slate-100">Accent Color</h2>
            <p className="text-xs text-slate-500 mt-0.5">
              Highlight color for active navigation, focused graph nodes, and interactive controls.
            </p>
          </div>
          <Palette className="w-4 h-4 text-slate-500" />
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
          {accentOptions.map((opt) => {
            const isSelected = accentColor === opt.value;
            return (
              <button
                key={opt.value}
                type="button"
                onClick={() => setAccentColor(opt.value)}
                className={`p-3 rounded-xl border text-left transition flex items-center gap-3 ${
                  isSelected
                    ? 'border-blue-500/80 bg-slate-800/80 text-white shadow-sm'
                    : 'border-slate-800/70 bg-slate-950/40 text-slate-400 hover:border-slate-700 hover:text-slate-200'
                }`}
              >
                <span
                  className="w-4 h-4 rounded-full flex-shrink-0 shadow-sm"
                  style={{ backgroundColor: opt.hex }}
                />
                <span className="text-xs font-medium truncate">{opt.label}</span>
              </button>
            );
          })}
        </div>
      </div>

      {/* 3. Workspace Density */}
      <div className="bg-slate-900/60 border border-slate-800/50 rounded-2xl p-6 backdrop-blur-md space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-base font-semibold text-slate-100">Layout Density</h2>
            <p className="text-xs text-slate-500 mt-0.5">Adjust spacing and sizing across workspaces.</p>
          </div>
          <Layout className="w-4 h-4 text-slate-500" />
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <button
            type="button"
            onClick={() => setDensity('comfortable')}
            className={`p-4 rounded-xl border text-left transition ${
              density === 'comfortable'
                ? 'border-blue-500/80 bg-blue-500/10 text-white'
                : 'border-slate-800/80 bg-slate-950/40 text-slate-400 hover:border-slate-700'
            }`}
          >
            <div className="font-semibold text-sm text-slate-200">Comfortable (Default)</div>
            <p className="text-xs text-slate-500 mt-1">Generous breathing room with large touch targets.</p>
          </button>

          <button
            type="button"
            onClick={() => setDensity('compact')}
            className={`p-4 rounded-xl border text-left transition ${
              density === 'compact'
                ? 'border-blue-500/80 bg-blue-500/10 text-white'
                : 'border-slate-800/80 bg-slate-950/40 text-slate-400 hover:border-slate-700'
            }`}
          >
            <div className="font-semibold text-sm text-slate-200">Compact</div>
            <p className="text-xs text-slate-500 mt-1">High-density information layout for multi-monitor setups.</p>
          </button>
        </div>
      </div>

      {/* 4. Engine & Backend Diagnostics */}
      <div className="bg-slate-900/60 border border-slate-800/50 rounded-2xl p-6 backdrop-blur-md space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-base font-semibold text-slate-100">Engine & Service Diagnostics</h2>
            <p className="text-xs text-slate-500 mt-0.5">Real-time status of backend microservices.</p>
          </div>
          <button
            type="button"
            onClick={handleRefreshHealth}
            disabled={isChecking}
            className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white transition text-xs font-medium flex items-center gap-1.5"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isChecking ? 'animate-spin' : ''}`} />
            Run Ping
          </button>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 pt-1">
          <div className="p-3 rounded-xl bg-slate-950/50 border border-slate-800/60 space-y-1">
            <span className="text-[10px] font-mono text-slate-500 uppercase tracking-wider block">API Endpoint</span>
            <div className="flex items-center gap-2">
              <span className={`w-2 h-2 rounded-full ${apiLive ? 'bg-emerald-400 animate-pulse' : 'bg-amber-400'}`} />
              <span className="text-sm font-semibold text-slate-200">{apiLive ? 'ONLINE' : 'MOCK LOCAL'}</span>
            </div>
            <span className="text-[11px] font-mono text-slate-500 block">http://127.0.0.1:8000</span>
          </div>

          <div className="p-3 rounded-xl bg-slate-950/50 border border-slate-800/60 space-y-1">
            <span className="text-[10px] font-mono text-slate-500 uppercase tracking-wider block">Latency</span>
            <div className="text-sm font-semibold font-mono text-slate-200">
              {apiLatency !== null ? `${apiLatency} ms` : 'N/A'}
            </div>
            <span className="text-[11px] text-slate-500 block">Roundtrip response time</span>
          </div>

          <div className="p-3 rounded-xl bg-slate-950/50 border border-slate-800/60 space-y-1">
            <span className="text-[10px] font-mono text-slate-500 uppercase tracking-wider block">Version</span>
            <div className="text-sm font-semibold text-slate-200">v2.0.0-pro</div>
            <span className="text-[11px] text-slate-500 block">Attribution & Pattern Engine</span>
          </div>
        </div>
      </div>
    </div>
  );
}