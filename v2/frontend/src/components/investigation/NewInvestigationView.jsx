import React, { useState } from 'react';
import { Search, Globe, Layers, Shield, Play, AlertTriangle, Zap } from 'lucide-react';
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
  const [useEtherscan, setUseEtherscan] = useState(true);
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
      <div className="min-h-[520px] flex items-center justify-center">
        <LoadingProgress
          targetAddress={addressInput || '0x...'}
          isLive={useEtherscan}
          maxHops={maxHops}
        />
      </div>
    );
  }

  return (
    <div className="max-w-2xl mx-auto py-8 px-4 sm:px-6 space-y-6">
      {/* Header */}
      <div className="text-center space-y-2">
        <h2 className="text-2xl sm:text-3xl font-extrabold text-slate-100 tracking-tight">
          Investigate a wallet
        </h2>
        <p className="text-sm text-slate-500 max-w-xl mx-auto leading-relaxed">
          Trace cryptocurrency movement and identify known services, entities and behavioral patterns.
        </p>
      </div>

      {/* Main form */}
      <form onSubmit={handleSubmit} className="space-y-4">
        {/* Target Address Input - large rounded */}
        <div className="space-y-2">
          <label className="text-sm font-medium text-slate-400 block mb-1.5">
            Target Ethereum Wallet Address
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
              className={`w-full pl-14 py-3 rounded-xl bg-slate-900 border border-slate-700 text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-2 transition ${
                validationError
                  ? 'focus:border-red-500 focus:ring-red-500/30'
                  : 'focus:border-slate-400 focus:ring-slate-500/30'
              }`}
            />
            <Search className="w-4.5 h-4.5 text-slate-500 absolute left-3.5 top-3.5" />
          </div>
          {validationError && (
            <div className="flex items-center gap-2 text-xs text-red-400 mt-1 font-mono">
              <AlertTriangle className="w-3 h-3 flex-shrink-0" />
              <span>{validationError}</span>
            </div>
          )}
        </div>

        {/* Configuration - compact, collapsed by default */}
        <div className="grid grid-cols-1 gap-3 pt-2">
          {/* Blockchain Network */}
          <div className="rounded-lg bg-slate-900/60 border border-slate-800/30 p-3 flex flex-col justify-between">
            <div className="flex items-center justify-between text-xs text-slate-500 font-medium">
              <span>Target Network</span>
              <Globe className="w-3.5 h-3.5 text-slate-400" />
            </div>
            <div className="mt-1">
              <span className="font-bold text-slate-200">Ethereum Mainnet</span>
              <span className="text-[9px] text-slate-500 block">Chain ID: 1</span>
            </div>
          </div>

          {/* Max Hops Depth */}
          <div className="rounded-lg bg-slate-900/60 border border-slate-800/30 p-3 flex flex-col justify-between">
            <div className="flex items-center justify-between text-xs text-slate-500 font-medium">
              <span>Maximum Hops Depth</span>
              <Layers className="w-3.5 h-3.5 text-slate-400" />
            </div>
            <div className="mt-1 flex items-center">
              <span className="font-bold text-slate-200">{maxHops} Hops</span>
              <span className="text-[9px] text-slate-500 mx-2">Standard Forensics</span>
              <input
                type="range"
                min="1"
                max="3"
                value={maxHops}
                onChange={(e) => setMaxHops(parseInt(e.target.value, 10))}
                className="w-24 h-1.5 bg-slate-800 rounded-lg appearance-none cursor-pointer mt-0.5"
              />
            </div>
          </div>

          {/* Live Data Toggle */}
          <div className="rounded-lg bg-slate-900/60 border border-slate-800/30 p-3 flex items-center justify-between">
            <div>
              <div className="flex items-center gap-1.5 text-xs text-slate-400 font-medium">
                <Zap className={`w-3.5 h-3.5 ${useEtherscan ? 'text-blue-400' : 'text-slate-500'}`} />
                <span>Live Blockchain Data</span>
              </div>
              <div className="mt-1">
                <span className="text-xs font-bold text-slate-200 block">Etherscan Live Trace</span>
                <span className="text-[10px] text-slate-500 block">Fetch live transaction history directly from Ethereum mainnet</span>
              </div>
            </div>
            <button
              type="button"
              onClick={() => setUseEtherscan(!useEtherscan)}
              className={`relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none ${
                useEtherscan ? 'bg-blue-600' : 'bg-slate-700'
              }`}
              title="Toggle Live Etherscan Data"
            >
              <span
                className={`pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out ${
                  useEtherscan ? 'translate-x-5' : 'translate-x-0'
                }`}
              />
            </button>
          </div>
        </div>

        {/* Primary Action Button */}
        <button
          type="submit"
          className="w-full py-3 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-100 text-sm font-medium transition flex items-center justify-center gap-2"
        >
          <Play className="w-3.5 h-3.5 fill-slate-100" />
          Start Investigation
        </button>
      </form>

      {/* Demo Presets - collapsed by default */}
      <div className="mt-4 pt-4 border-t border-slate-800/30">
        <h3 className="text-[9px] font-medium uppercase tracking-wider text-slate-500 block mb-2">Forensic Target Presets</h3>
        <div className="grid grid-cols-1 gap-2">
          {DEMO_PRESETS.map((preset, idx) => (
            <div
              key={idx}
              onClick={() => handleSelectPreset(preset.address)}
              className="rounded-lg bg-slate-900/60 border border-slate-800/30 cursor-pointer hover:border-slate-600/40 transition p-2.5 text-left"
            >
              <span className="text-[9px] font-semibold text-slate-300 group-hover:text-slate-100 transition truncate" title={preset.label}>
                {preset.label}
              </span>
              <p className="text-[10px] text-slate-500/60 mt-0.5 truncate">{preset.address}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}