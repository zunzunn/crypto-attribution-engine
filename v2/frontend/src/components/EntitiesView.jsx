import React, { useState } from 'react';
import { Database, Search, Shield, Filter, ExternalLink, ArrowUpRight } from 'lucide-react';
import { shortenAddress, getEntityBadgeStyle } from '../utils/formatters';

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

  const filtered = REGISTRY_ENTITIES.filter(item => {
    const matchesSearch = item.entity.toLowerCase().includes(searchTerm.toLowerCase()) || item.address.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesFilter = filterType === 'ALL' || item.type.toUpperCase() === filterType.toUpperCase();
    return matchesSearch && matchesFilter;
  });

  return (
    <div className="space-y-6">
      
      {/* Header */}
      <div className="glass-panel p-5 rounded-xl border border-slate-800 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-white flex items-center gap-2">
            <Database className="w-5 h-5 text-cyan-400" />
            Address Attribution Registry
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Verified service provider intelligence, mixer addresses, VASP endpoints & scam labels.
          </p>
        </div>

        {/* Filters */}
        <div className="flex items-center gap-2 w-full sm:w-auto">
          <div className="relative flex-1 sm:w-64">
            <input
              type="text"
              placeholder="Search by entity name or address..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-9 pr-4 py-1.5 text-xs rounded-lg bg-slate-950 border border-slate-700/80 text-white placeholder-slate-500 focus:outline-none focus:border-cyan-500"
            />
            <Search className="w-4 h-4 text-slate-500 absolute left-2.5 top-2" />
          </div>

          <select
            value={filterType}
            onChange={(e) => setFilterType(e.target.value)}
            className="px-3 py-1.5 text-xs rounded-lg bg-slate-950 border border-slate-700/80 text-slate-300 focus:outline-none focus:border-cyan-500 font-sans"
          >
            <option value="ALL">All Categories</option>
            <option value="VASP">VASPs / Exchanges</option>
            <option value="MIXER">Mixers</option>
            <option value="BRIDGE">Bridges</option>
            <option value="SCAM/FRAUD">Scams / Fraud</option>
          </select>
        </div>
      </div>

      {/* Entity Table */}
      <div className="glass-panel rounded-xl border border-slate-800 p-5">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs text-slate-300">
            <thead className="bg-slate-900/80 text-slate-400 border-b border-slate-800 uppercase font-mono text-[10px]">
              <tr>
                <th className="px-4 py-3">Entity Name</th>
                <th className="px-4 py-3">Category</th>
                <th className="px-4 py-3">Ethereum Address</th>
                <th className="px-4 py-3">Source Provenance</th>
                <th className="px-4 py-3">Confidence</th>
                <th className="px-4 py-3 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 font-mono">
              {filtered.map((item, idx) => (
                <tr key={idx} className="hover:bg-slate-900/50 transition">
                  <td className="px-4 py-3 font-sans font-bold text-white">{item.entity}</td>
                  <td className="px-4 py-3">
                    <span className={`px-2 py-0.5 text-[11px] font-semibold rounded border ${getEntityBadgeStyle(item.type)}`}>
                      {item.type}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-slate-300">{shortenAddress(item.address, 10, 8)}</td>
                  <td className="px-4 py-3 font-sans text-slate-400">{item.source}</td>
                  <td className="px-4 py-3 font-bold text-cyan-400">{(item.confidence * 100).toFixed(0)}%</td>
                  <td className="px-4 py-3 text-right">
                    <button
                      onClick={() => onSelectEntity(item.address)}
                      className="inline-flex items-center gap-1 px-3 py-1 text-xs font-sans font-medium rounded-lg bg-cyan-500/20 text-cyan-300 hover:bg-cyan-500/30 border border-cyan-500/40 transition"
                    >
                      Trace <ArrowUpRight className="w-3 h-3" />
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
