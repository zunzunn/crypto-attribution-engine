import React, { useState } from 'react';
import { Database, Search, ArrowUpRight } from 'lucide-react';
import { shortenAddress } from '../utils/formatters';
import EntityBadge from './common/EntityBadge';

const REGISTRY_ENTITIES = [
  { address: "0x1111111111111111111111111111111111111111", entity: "TornadoCash_Vault_0.1", type: "Mixer", source: "Local Intelligence + OFAC", confidence: 1.0 },
  { address: "0x3333333333333333333333333333333333333333", entity: "Binance_Hot_Wallet_14", type: "VASP", source: "Etherscan Name Tag", confidence: 1.0 },
  { address: "0x2222222222222222222222222222222222222222", entity: "Arbitrum_Bridge_L1", type: "Bridge", source: "Local Registry", confidence: 0.90 },
  { address: "0x5555555555555555555555555555555555555555", entity: "OKX_Deposit_Wallet", type: "VASP", source: "Local Registry", confidence: 0.95 },
  { address: "0x6666666666666666666666666666666666666666", entity: "Kraken_Hot_Wallet", type: "VASP", source: "Etherscan Name Tag", confidence: 1.0 },
  { address: "0x71C7656EC7ab88b098defB751B7401B5f6d8976F", entity: "Phishing_Drainer_Wallet", type: "Scam/Fraud", source: "SIH Cybercrime Portal", confidence: 0.95 },
  { address: "0x0000000000000000000000000000000000000000", entity: "Null_Burn_Address", type: "Unknown", source: "Protocol Constants", confidence: 1.0 },
  { address: "0xdAC17F958D2ee523a2206206994597C13D831ec7", entity: "Tether_USDT_Contract", type: "Token", source: "ERC-20 Registry", confidence: 1.0 }
];

export default function EntitiesView({ onSelectEntity }) {
  const [searchTerm, setSearchTerm] = useState('');
  const [filterType, setFilterType] = useState('ALL');

  const filtered = REGISTRY_ENTITIES.filter((item) => {
    const term = searchTerm.toLowerCase();
    const matchesSearch =
      item.entity.toLowerCase().includes(term) ||
      item.address.toLowerCase().includes(term) ||
      item.source.toLowerCase().includes(term);

    const matchesFilter =
      filterType === 'ALL' || item.type.toUpperCase().includes(filterType.toUpperCase());

    return matchesSearch && matchesFilter;
  });

  const vaspCount = REGISTRY_ENTITIES.filter((e) => e.type.toUpperCase().includes('VASP')).length;
  const mixerCount = REGISTRY_ENTITIES.filter((e) => e.type.toUpperCase().includes('MIXER')).length;
  const bridgeCount = REGISTRY_ENTITIES.filter((e) => e.type.toUpperCase().includes('BRIDGE')).length;
  const scamCount = REGISTRY_ENTITIES.filter((e) => e.type.toUpperCase().includes('SCAM') || e.type.toUpperCase().includes('FRAUD')).length;

  return (
    <div className="space-y-6">
      {/* Top Header */}
      <div className="cyber-panel p-5 sm:p-6 rounded-2xl border border-slate-800/80 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <div className="p-2 rounded-xl bg-blue-500/10 text-blue-400 border border-blue-500/30">
              <Database className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-xl font-bold text-white tracking-wide">
                Address Attribution Registry
              </h2>
              <p className="text-xs text-slate-400 mt-0.5">
                Verified exchange deposit endpoints, sanctioned mixer contracts, canonical bridges & scam drainers
              </p>
            </div>
          </div>
        </div>

        {/* Category Stat Pills */}
        <div className="flex flex-wrap items-center gap-2 text-xs font-mono">
          <span className="px-2.5 py-1 rounded-lg bg-blue-500/10 text-blue-400 border border-blue-500/30">
            {vaspCount} Exchanges
          </span>
          <span className="px-2.5 py-1 rounded-lg bg-red-500/10 text-red-400 border border-red-500/30">
            {mixerCount} Mixers
          </span>
          <span className="px-2.5 py-1 rounded-lg bg-amber-500/10 text-amber-400 border border-amber-500/30">
            {bridgeCount} Bridges
          </span>
          <span className="px-2.5 py-1 rounded-lg bg-purple-500/10 text-purple-400 border border-purple-500/30">
            {scamCount} Scams
          </span>
        </div>
      </div>

      {/* Filter & Search Bar */}
      <div className="cyber-panel p-4 rounded-xl border border-slate-800/80 flex flex-col sm:flex-row items-center justify-between gap-3">
        <div className="relative flex-1 w-full sm:w-80">
          <input
            type="text"
            placeholder="Search entity name, Ethereum address, or provenance source..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-9 pr-4 py-1.5 text-xs font-mono rounded-lg bg-slate-950 border border-slate-700/80 text-white placeholder-slate-500 focus:outline-none focus:border-cyan-500"
          />
          <Search className="w-3.5 h-3.5 text-slate-500 absolute left-3 top-2" />
        </div>

        <div className="flex items-center gap-2 w-full sm:w-auto">
          <select
            value={filterType}
            onChange={(e) => setFilterType(e.target.value)}
            className="px-3 py-1.5 text-xs rounded-lg bg-slate-950 border border-slate-700/80 text-slate-300 focus:outline-none focus:border-cyan-500 font-mono"
          >
            <option value="ALL">All Categories</option>
            <option value="VASP">Exchanges & VASPs</option>
            <option value="MIXER">Mixers & Privacy Pools</option>
            <option value="BRIDGE">Cross-Chain Bridges</option>
            <option value="SCAM">Scams & Drainers</option>
          </select>

          <span className="text-xs font-mono text-slate-500">
            {filtered.length} of {REGISTRY_ENTITIES.length} entities
          </span>
        </div>
      </div>

      {/* Entity Table */}
      <div className="cyber-panel rounded-xl border border-slate-800/80 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs font-mono text-slate-300">
            <thead className="bg-slate-950/80 text-slate-400 border-b border-slate-800 uppercase text-[10px] tracking-wider">
              <tr>
                <th className="px-4 py-3">Entity Name</th>
                <th className="px-4 py-3">Category</th>
                <th className="px-4 py-3">Ethereum Address</th>
                <th className="px-4 py-3">Source Provenance</th>
                <th className="px-4 py-3">Confidence</th>
                <th className="px-4 py-3 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {filtered.map((item, idx) => (
                <tr key={idx} className="hover:bg-slate-900/50 transition">
                  <td className="px-4 py-3 font-sans font-bold text-white">
                    {item.entity}
                  </td>
                  <td className="px-4 py-3">
                    <EntityBadge type={item.type} size="xs" />
                  </td>
                  <td className="px-4 py-3 text-slate-300">
                    {shortenAddress(item.address, 10, 8)}
                  </td>
                  <td className="px-4 py-3 font-sans text-slate-400">
                    {item.source}
                  </td>
                  <td className="px-4 py-3 font-bold text-cyan-400">
                    {(item.confidence * 100).toFixed(0)}%
                  </td>
                  <td className="px-4 py-3 text-right">
                    <button
                      onClick={() => onSelectEntity(item.address)}
                      className="inline-flex items-center gap-1 px-3 py-1 text-xs font-sans font-medium rounded-lg bg-cyan-500/15 text-cyan-300 hover:bg-cyan-500/25 border border-cyan-500/30 transition shadow-sm"
                    >
                      Investigate <ArrowUpRight className="w-3 h-3" />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
