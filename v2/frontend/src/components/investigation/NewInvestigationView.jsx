import React, { useState } from 'react';
import {
  Search,
  Play,
  Layers,
  Zap,
  Globe,
  AlertCircle,
  Sparkles,
  ArrowRight
} from 'lucide-react';
import { isValidEthAddress } from '../../utils/formatters';
import LoadingProgress from '../common/LoadingProgress';

const DEMO_PRESETS = [
  {
    label: 'Phishing Drainer (SIH Cybercrime Case)',
    address: '0x71C7656EC7ab88b098defB751B7401B5f6d8976F',
    tags: ['Phishing', 'Mixer Interaction', 'Critical Risk']
  },
  {
    label: 'vitalik.eth (High Volume Hub)',
    address: '0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045',
    tags: ['Named Entity', 'Complex Topology']
  },
  {
    label: 'Binance Hot Wallet 14',
    address: '0x3333333333333333333333333333333333333333',
    tags: ['Exchange VASP', 'High Liquidity']
  },
  {
    label: 'Arbitrum Canonical Bridge L1',
    address: '0x2222222222222222222222222222222222222222',
    tags: ['Cross-Chain Bridge', 'Multi-Asset']
  }
];

export default function NewInvestigationView({ onStartInvestigation, isExecuting = false }) {
  const [addressInput, setAddressInput] = useState('');
  const [maxHops, setMaxHops] = useState(2);
  const [useEtherscan, setUseEtherscan] = useState(false);
  const [validationError, setValidationError] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    const cleanAddr = addressInput.trim();

    if (!cleanAddr) {
      setValidationError('Please enter a target Ethereum wallet address to investigate.');
      return;
    }

    if (!isValidEthAddress(cleanAddr)) {
      setValidationError('Invalid Ethereum address format. Must begin with 0x followed by 40 hex characters.');
      return;
    }

    setValidationError('');
    onStartInvestigation(cleanAddr, maxHops, useEtherscan);
  };

  const handleSelectPreset = (addr) => {
    setAddressInput(addr);
    setValidationError('');
  };

  if (isExecuting) {
    return (
      <div className="py-12 px-4 flex items-center justify-center min-h-[520px]">
        <LoadingProgress
          targetAddress={addressInput || '0x...'}
          isLive={useEtherscan}
          maxHops={maxHops}
        />
      </div>
    );
  }

  return (
    <div className="max-w-3xl mx-auto py-8 px-4 sm:px-6 space-y-8">
      {/* Header Banner */}
      <div className="text-center space-y-2">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-cyan-500/10 border border-cyan-500/30 text-cyan-400 text-xs font-mono font-semibold uppercase tracking-wider">
          <Sparkles className="w-3.5 h-3.5" />
          Autonomous On-Chain Forensics
        </div>
        <h2 className="text-3xl sm:text-4xl font-extrabold text-white tracking-tight">
          Initialize New Investigation
        </h2>
        <p className="text-xs sm:text-sm text-slate-400 max-w-xl mx-auto leading-relaxed">
          Execute multi-hop transaction tracing, entity attribution, evidence-weighted risk scoring, and behavioral obfuscation detection.
        </p>
      </div>

      {/* Main Investigation Launch Card */}
      <div className="cyber-panel rounded-2xl p-6 sm:p-8 border border-slate-700/80 shadow-2xl relative overflow-hidden">
        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Target Address Input */}
          <div className="space-y-2">
            <label className="text-xs font-mono uppercase tracking-wider text-slate-300 font-bold block flex items-center justify-between">
              <span>Target Ethereum Wallet Address</span>
              <span className="text-[11px] text-slate-500 font-normal">Format: 0x... (42 chars)</span>
            </label>
            <div className="relative">
              <input
                type="text"
                value={addressInput}
                onChange={(e) => {
                  setAddressInput(e.target.value);
                  if (validationError) setValidationError('');
                }}
                placeholder="Enter suspect wallet address: 0x..."
                className={`w-full pl-11 pr-4 py-3.5 text-sm font-mono rounded-xl bg-slate-950/90 border text-white placeholder-slate-500 focus:outline-none focus:ring-2 transition ${
                  validationError
                    ? 'border-red-500/80 focus:border-red-500 focus:ring-red-500/30'
                    : 'border-slate-700/80 focus:border-cyan-500/80 focus:ring-cyan-500/30'
                }`}
              />
              <Search className="w-5 h-5 text-slate-500 absolute left-3.5 top-4" />
            </div>
            {validationError && (
              <div className="flex items-center gap-2 text-xs text-red-400 mt-1 font-mono">
                <AlertCircle className="w-4 h-4 flex-shrink-0" />
                <span>{validationError}</span>
              </div>
            )}
          </div>

          {/* Configuration Grid */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 pt-2 border-t border-slate-800/80">
            {/* Blockchain Network */}
            <div className="cyber-card p-4 rounded-xl border border-slate-800 flex flex-col justify-between">
              <div className="flex items-center justify-between text-xs text-slate-400 font-medium">
                <span>Target Network</span>
                <Globe className="w-4 h-4 text-cyan-400" />
              </div>
              <div className="mt-2">
                <div className="text-xs font-bold text-white flex items-center gap-1.5">
                  <span className="w-2 h-2 rounded-full bg-emerald-400" />
                  Ethereum Mainnet
                </div>
                <span className="text-[10px] text-slate-500 font-mono block mt-0.5">Chain ID: 1</span>
              </div>
            </div>

            {/* Max Hops Depth */}
            <div className="cyber-card p-4 rounded-xl border border-slate-800 flex flex-col justify-between">
              <div className="flex items-center justify-between text-xs text-slate-400 font-medium">
                <span>Maximum Hops Depth</span>
                <Layers className="w-4 h-4 text-cyan-400" />
              </div>
              <div className="mt-2">
                <div className="flex items-center justify-between text-xs font-bold text-white mb-1.5 font-mono">
                  <span>{maxHops} Hops</span>
                  <span className="text-[10px] text-cyan-400">
                    {maxHops === 1 ? 'Direct Peers' : maxHops === 2 ? 'Standard Forensics' : 'Deep Graph'}
                  </span>
                </div>
                <input
                  type="range"
                  min="1"
                  max="4"
                  value={maxHops}
                  onChange={(e) => setMaxHops(parseInt(e.target.value, 10))}
                  className="w-full h-1.5 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-cyan-400"
                />
              </div>
            </div>

            {/* Live Data Toggle */}
            <div className="cyber-card p-4 rounded-xl border border-slate-800 flex flex-col justify-between">
              <div className="flex items-center justify-between text-xs text-slate-400 font-medium">
                <span>Live Blockchain Data</span>
                <Zap className="w-4 h-4 text-cyan-400" />
              </div>
              <div className="mt-2 flex items-center justify-between">
                <div>
                  <span className="text-xs font-bold text-white block">Etherscan API</span>
                  <span className="text-[10px] text-slate-500 block">Live transfer logs</span>
                </div>
                <label className="relative inline-flex items-center cursor-pointer">
                  <input
                    type="checkbox"
                    checked={useEtherscan}
                    onChange={(e) => setUseEtherscan(e.target.checked)}
                    className="sr-only peer"
                  />
                  <div className="w-9 h-5 bg-slate-800 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-slate-300 after:border after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-cyan-500"></div>
                </label>
              </div>
            </div>
          </div>

          {/* Primary Action Button */}
          <div className="pt-2">
            <button
              type="submit"
              className="w-full py-3.5 px-6 rounded-xl bg-gradient-to-r from-cyan-500 via-blue-600 to-cyan-500 hover:from-cyan-400 hover:to-blue-500 text-white font-bold text-sm tracking-wide shadow-xl shadow-cyan-950/60 flex items-center justify-center gap-2.5 transition transform active:scale-[0.99]"
            >
              <Play className="w-4 h-4 fill-white" />
              Start Investigation
            </button>
          </div>
        </form>
      </div>

      {/* Recommended Investigation Targets */}
      <div className="space-y-3">
        <h3 className="text-xs font-mono uppercase tracking-wider text-slate-400 font-bold px-1">
          Forensic Target Presets
        </h3>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          {DEMO_PRESETS.map((preset, idx) => (
            <div
              key={idx}
              onClick={() => handleSelectPreset(preset.address)}
              className="cyber-card p-3.5 rounded-xl border border-slate-800/80 cursor-pointer hover:border-cyan-500/40 transition group"
            >
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-white group-hover:text-cyan-300 transition">
                  {preset.label}
                </span>
                <ArrowRight className="w-3.5 h-3.5 text-slate-500 group-hover:text-cyan-400 group-hover:translate-x-0.5 transition" />
              </div>
              <p className="text-[11px] font-mono text-slate-400 mt-1 truncate">
                {preset.address}
              </p>
              <div className="flex flex-wrap gap-1.5 mt-2">
                {preset.tags.map((tag, tIdx) => (
                  <span
                    key={tIdx}
                    className="text-[9px] font-mono px-1.5 py-0.2 rounded bg-slate-900 border border-slate-800 text-slate-400"
                  >
                    {tag}
                  </span>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
