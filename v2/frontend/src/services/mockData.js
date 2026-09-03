export const MOCK_TRACE_DATA = {
  target_address: "0x71C7656EC7ab88b098defB751B7401B5f6d8976F",
  max_hops: 3,
  graph: {
    "0x71C7656EC7ab88b098defB751B7401B5f6d8976F": [
      { to: "0x1111111111111111111111111111111111111111", amount: "45.50", asset_type: "ETH", hash: "0xa1b2c3d4e5f67890", timestamp: 1725380000 },
      { to: "0x2222222222222222222222222222222222222222", amount: "10000.00", asset_type: "ERC20", symbol: "USDT", hash: "0xb2c3d4e5f67890a1", timestamp: 1725380500 },
      { to: "0x3333333333333333333333333333333333333333", amount: "12.00", asset_type: "ETH", hash: "0xc3d4e5f67890a1b2", timestamp: 1725381000 }
    ],
    "0x1111111111111111111111111111111111111111": [
      { to: "0x4444444444444444444444444444444444444444", amount: "45.00", asset_type: "ETH", hash: "0xd4e5f67890a1b2c3", timestamp: 1725381200 }
    ],
    "0x2222222222222222222222222222222222222222": [
      { to: "0x5555555555555555555555555555555555555555", amount: "9950.00", asset_type: "ERC20", symbol: "USDT", hash: "0xe5f67890a1b2c3d4", timestamp: 1725381800 }
    ],
    "0x4444444444444444444444444444444444444444": [
      { to: "0x6666666666666666666666666666666666666666", amount: "44.20", asset_type: "ETH", hash: "0xf67890a1b2c3d4e5", timestamp: 1725382500 }
    ]
  },
  trace_results: {
    discovered_addresses: [
      {
        address: "0x71C7656EC7ab88b098defB751B7401B5f6d8976F",
        entity: "Phishing_Drainer_Wallet",
        entity_type: "Scam/Fraud",
        confidence: 0.95,
        sources: ["Local Registry", "Etherscan Tag"],
        hop_distance: 0,
        evidence: "Flagged in SIH Cyber Crime Victim Report #2026-8812",
        risk: {
          score: 85.0,
          risk_level: "Critical",
          reasons: ["Target address directly implicated in scam/phishing drain", "High confidence threat intelligence tag"]
        }
      },
      {
        address: "0x1111111111111111111111111111111111111111",
        entity: "TornadoCash_Vault_0.1",
        entity_type: "Mixer",
        confidence: 1.0,
        sources: ["Local Registry"],
        hop_distance: 1,
        evidence: "Identified smart contract address for privacy mixer deposit pool",
        risk: {
          score: 76.0,
          risk_level: "Critical",
          reasons: ["Interaction with OFAC-sanctioned privacy mixer contract", "Reached within 1 hop distance"]
        }
      },
      {
        address: "0x2222222222222222222222222222222222222222",
        entity: "Arbitrum_Bridge_L1",
        entity_type: "Bridge",
        confidence: 0.90,
        sources: ["Etherscan Metadata"],
        hop_distance: 1,
        evidence: "Cross-chain canonical bridge smart contract",
        risk: {
          score: 37.0,
          risk_level: "Medium",
          reasons: ["Cross-chain bridge interaction detected", "Hop distance penalty applied"]
        }
      },
      {
        address: "0x3333333333333333333333333333333333333333",
        entity: "Binance_Hot_Wallet_14",
        entity_type: "VASP",
        confidence: 1.0,
        sources: ["Local Registry", "Etherscan Metadata"],
        hop_distance: 1,
        evidence: "Centralized VASP exchange deposit address",
        risk: {
          score: 17.0,
          risk_level: "Low",
          reasons: ["Verified VASP exchange endpoint", "High confidence service identity"]
        }
      },
      {
        address: "0x4444444444444444444444444444444444444444",
        entity: "Unknown_Intermediary_Wallet",
        entity_type: "Unknown",
        confidence: 0.0,
        sources: [],
        hop_distance: 2,
        evidence: "Unlabeled un-attributed wallet address",
        risk: {
          score: 6.0,
          risk_level: "Low",
          reasons: ["Unattributed hop address"]
        }
      },
      {
        address: "0x5555555555555555555555555555555555555555",
        entity: "OKX_Deposit_Wallet",
        entity_type: "VASP",
        confidence: 0.95,
        sources: ["Local Registry"],
        hop_distance: 2,
        evidence: "Centralized Exchange VASP deposit wallet",
        risk: {
          score: 14.0,
          risk_level: "Low",
          reasons: ["VASP deposit destination"]
        }
      },
      {
        address: "0x6666666666666666666666666666666666666666",
        entity: "Kraken_Hot_Wallet",
        entity_type: "VASP",
        confidence: 1.0,
        sources: ["Etherscan Metadata"],
        hop_distance: 3,
        evidence: "Centralized Exchange VASP endpoint",
        risk: {
          score: 11.0,
          risk_level: "Low",
          reasons: ["VASP terminal destination"]
        }
      }
    ]
  },
  patterns: {
    summary: {
      total_patterns_detected: 4,
      has_fan_out: true,
      has_fan_in: false,
      has_rapid_hopping: true,
      has_layering: true
    },
    fan_out_events: [
      {
        address: "0x71C7656EC7ab88b098defB751B7401B5f6d8976F",
        recipient_count: 3,
        recipients: [
          "0x1111111111111111111111111111111111111111",
          "0x2222222222222222222222222222222222222222",
          "0x3333333333333333333333333333333333333333"
        ],
        total_outbound_amount: 57.5,
        transaction_count: 3,
        pattern_type: "FAN_OUT_SPLITTING",
        risk_signal: "HIGH_FAN_OUT",
        description: "Address split stolen funds into 3 distinct outbound paths (Mixer, Bridge, VASP)."
      }
    ],
    fan_in_events: [],
    rapid_hopping_events: [
      {
        hop_1_from: "0x71C7656EC7ab88b098defB751B7401B5f6d8976F",
        intermediate_address: "0x1111111111111111111111111111111111111111",
        hop_2_to: "0x4444444444444444444444444444444444444444",
        time_delta_seconds: 700,
        pattern_type: "RAPID_WALLET_HOPPING",
        description: "Funds routed through TornadoCash mixer vault in 700 seconds (< 15 mins)."
      },
      {
        hop_1_from: "0x71C7656EC7ab88b098defB751B7401B5f6d8976F",
        intermediate_address: "0x2222222222222222222222222222222222222222",
        hop_2_to: "0x5555555555555555555555555555555555555555",
        time_delta_seconds: 1300,
        pattern_type: "RAPID_WALLET_HOPPING",
        description: "Funds moved across Arbitrum bridge contract to OKX deposit in 1300 seconds."
      }
    ],
    layering_events: [
      {
        max_hop_depth: 3,
        deep_address_count: 1,
        addresses: ["0x6666666666666666666666666666666666666666"],
        pattern_type: "MULTI_HOP_LAYERING",
        description: "Funds traversed 3 sequential hop layers before terminating at Kraken VASP."
      }
    ]
  },
  report_summary: {
    total_addresses_traced: 7,
    maximum_hop_distance: 3,
    attributed_entities_count: 6,
    highest_risk_score: 85.0,
    highest_risk_level: "Critical",
    patterns_detected_count: 4
  }
};

export const MOCK_DASHBOARD_METRICS = {
  total_investigations: 48,
  active_investigations: 12,
  high_risk_wallets: 15,
  known_entities_count: 64,
  risk_distribution: [
    { name: "Critical", value: 8, color: "#ef4444" },
    { name: "High", value: 14, color: "#f43f5e" },
    { name: "Medium", value: 18, color: "#f59e0b" },
    { name: "Low", value: 24, color: "#10b981" }
  ],
  asset_breakdown: [
    { asset: "ETH", volume: 142.8, color: "#627eea" },
    { asset: "USDT", volume: 485000, color: "#26a17b" },
    { asset: "USDC", volume: 210000, color: "#2775ca" },
    { asset: "Internal ETH", volume: 68.4, color: "#8b5cf6" }
  ],
  recent_investigations: [
    { id: "INV-2026-081", address: "0x71C7656EC7ab88b098defB751B7401B5f6d8976F", risk: "Critical", score: 85.0, entity: "Phishing Drainer", hops: 3, date: "2026-09-03" },
    { id: "INV-2026-080", address: "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045", risk: "Low", score: 12.0, entity: "vitalik.eth", hops: 2, date: "2026-09-02" },
    { id: "INV-2026-079", address: "0x098B716B8Aaf21512996dC57EB0615e2383E2f96", risk: "High", score: 72.5, entity: "Hacker_Drainer_V2", hops: 4, date: "2026-09-01" },
    { id: "INV-2026-078", address: "0x3fC91A3afd70395Cd496C647d5a6CC9D4B2b7FAD", risk: "Medium", score: 42.0, entity: "Uniswap_Universal_Router", hops: 1, date: "2026-08-31" }
  ]
};
