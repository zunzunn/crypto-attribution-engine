import axios from 'axios';
import { MOCK_TRACE_DATA } from './mockData.js';

const API_BASE_URL = (typeof import.meta !== 'undefined' && import.meta.env?.VITE_API_BASE_URL) || 'http://127.0.0.1:8000';

const client = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json'
  }
});

function normalizeTraceResponse(rawResponse) {
  if (!rawResponse || typeof rawResponse !== 'object') return rawResponse;
  const traceResults = rawResponse.trace_results || {};
  const attribution = traceResults.attribution || {};

  let discoveredAddresses = traceResults.discovered_addresses;
  if (!Array.isArray(discoveredAddresses) || discoveredAddresses.length === 0) {
    const discovered = traceResults.discovered || Object.keys(attribution);
    discoveredAddresses = discovered.map((addr) => {
      const lower = (addr || '').toLowerCase();
      const info = attribution[addr] || attribution[lower] || {};
      const hop = traceResults.paths?.[addr]?.[2] ?? info.hop_distance ?? 0;
      return {
        address: info.address || addr,
        entity: info.entity_name || 'Unknown',
        entity_type: info.entity_type || 'Unknown',
        confidence: info.confidence || 0,
        sources: info.source ? [info.source] : (info.attribution_source || []),
        hop_distance: hop,
        evidence: info.evidence || '',
        risk: {
          score: info.risk_score || 0,
          risk_level: info.risk_level || 'Low',
          reasons: info.risk_evidence ? [info.risk_evidence] : (info.risk_reasons || [])
        }
      };
    });
  }

  const normalizedGraph = {};
  const rawGraph = rawResponse.graph || {};
  Object.entries(rawGraph).forEach(([edgeKey, txList]) => {
    if (!edgeKey.includes('->')) {
      normalizedGraph[edgeKey] = txList;
      return;
    }
    const parts = edgeKey.split('->');
    if (parts.length !== 2) return;
    const [fromAddr, toAddr] = parts;
    normalizedGraph[fromAddr] = (normalizedGraph[fromAddr] || []).concat(
      (txList || []).map((tx) => ({
        to: tx.to_address || tx.to || toAddr,
        amount: tx.amount ?? tx.value_eth ?? 0,
        asset_type: tx.asset_type || 'ETH',
        symbol: tx.symbol || 'ETH',
        hash: tx.hash || '',
        timestamp: tx.timestamp || 0
      }))
    );
  });

  return {
    ...rawResponse,
    trace_results: {
      ...traceResults,
      discovered_addresses: discoveredAddresses
    },
    graph: normalizedGraph
  };
}

export async function checkApiHealth() {
  const startTime = Date.now();
  try {
    const res = await client.get('/');
    const latency = Date.now() - startTime;
    return { isLive: true, latency, data: res.data };
  } catch (err) {
    return { isLive: false, latency: null, data: null, error: err.message };
  }
}

export async function fetchAddressTrace(targetAddress, maxHops = 2, useEtherscan = false) {
  try {
    const res = await client.post('/api/v2/trace', {
      target_address: targetAddress,
      max_hops: maxHops,
      use_etherscan: useEtherscan
    });
    return { isLive: true, data: normalizeTraceResponse(res.data) };
  } catch (err) {
    console.warn("Backend API offline or unreachable. Using fallback mock trace dataset.", err.message);
    const fallbackData = { ...MOCK_TRACE_DATA, target_address: targetAddress };
    return { isLive: false, data: fallbackData, error: err.message };
  }
}

export async function lookupAddressIntelligence(address) {
  try {
    const res = await client.get(`/api/v2/address/${address}`);
    return { isLive: true, data: res.data };
  } catch (err) {
    const mockNode = MOCK_TRACE_DATA.trace_results.discovered_addresses.find(
      n => n.address.toLowerCase() === address.toLowerCase()
    );
    if (mockNode) {
      return {
        isLive: false,
        data: {
          address: mockNode.address,
          attribution: {
            entity_name: mockNode.entity,
            entity_type: mockNode.entity_type,
            confidence: mockNode.confidence,
            sources: mockNode.sources,
            evidence: mockNode.evidence
          },
          risk: mockNode.risk
        }
      };
    }
    return {
      isLive: false,
      data: {
        address,
        attribution: { entity_name: "Unknown", entity_type: "Unknown", confidence: 0, sources: [] },
        risk: { score: 0, risk_level: "Low", reasons: ["Unattributed target address"] }
      }
    };
  }
}

export async function fetchInvestigationReport(targetAddress, traceResults, patterns, caseId = 'CASE-2026-001') {
  try {
    const res = await client.post('/api/v2/report', {
      target_address: targetAddress,
      trace_results: traceResults,
      patterns: patterns,
      case_id: caseId,
      network: "Ethereum Mainnet"
    });
    return { isLive: true, data: res.data };
  } catch (err) {
    return {
      isLive: false,
      data: {
        json_report: {
          case_metadata: {
            case_id: caseId,
            target_address: targetAddress,
            network: "Ethereum Mainnet",
            generated_at: new Date().toISOString()
          },
          investigation_summary: MOCK_TRACE_DATA.report_summary,
          attributed_entities: MOCK_TRACE_DATA.trace_results.discovered_addresses.filter(n => n.entity !== "Unknown"),
          detected_behavioral_patterns: MOCK_TRACE_DATA.patterns,
          disclaimer: "Investigative priority report derived from fallback mock environment."
        },
        markdown_report: `# Crypto Attribution & Forensic Investigation Report\n\n**Case ID:** \`${caseId}\`\n**Target Address:** \`${targetAddress}\`\n\n## Summary\n- Total Traced: ${MOCK_TRACE_DATA.report_summary.total_addresses_traced}\n- Max Hops: ${MOCK_TRACE_DATA.report_summary.maximum_hop_distance}\n- Highest Risk: **${MOCK_TRACE_DATA.report_summary.highest_risk_level}** (${MOCK_TRACE_DATA.report_summary.highest_risk_score}/100)`
      }
    };
  }
}

export const EMPTY_DASHBOARD_METRICS = {
  total_investigations: 0,
  active_investigations: 0,
  high_risk_wallets: 0,
  known_entities_count: 0,
  obfuscation_patterns_count: 0,
  risk_distribution: [
    { name: "Critical", value: 0, color: "#ef4444" },
    { name: "High", value: 0, color: "#f43f5e" },
    { name: "Medium", value: 0, color: "#f59e0b" },
    { name: "Low", value: 0, color: "#10b981" }
  ],
  asset_breakdown: [],
  recent_investigations: [],
  highest_risk_level: "N/A",
  highest_risk_score: 0,
  obfuscation_pattern_labels: []
};

const ASSET_COLORS = {
  ETH: "#627eea",
  "Internal ETH": "#8b5cf6",
  INTERNAL_ETH: "#8b5cf6",
  ERC20: "#26a17b",
  USDT: "#26a17b",
  USDC: "#2775ca"
};

function buildAssetBreakdown(graph) {
  if (!graph || typeof graph !== 'object') return [];
  const totals = {};
  Object.entries(graph).forEach(([, txList]) => {
    (txList || []).forEach((tx) => {
      const assetType = tx.asset_type || 'ETH';
      const symbol = tx.symbol || (assetType === 'ERC20' ? 'ERC20' : 'ETH');
      let displayKey = assetType;
      if (assetType === 'ETH') displayKey = 'ETH';
      else if (assetType === 'INTERNAL_ETH') displayKey = 'Internal ETH';
      else if (assetType === 'ERC20') displayKey = symbol || 'ERC20';

      const amount = parseFloat(tx.amount);
      if (!Number.isFinite(amount) || amount <= 0) return;
      totals[displayKey] = (totals[displayKey] || 0) + amount;
    });
  });

  return Object.entries(totals)
    .map(([asset, volume]) => ({
      asset,
      volume: Math.round(volume * 100) / 100,
      color: ASSET_COLORS[asset] || '#64748b'
    }))
    .sort((a, b) => b.volume - a.volume);
}

function buildRiskDistribution(discoveredAddresses) {
  const dist = { Critical: 0, High: 0, Medium: 0, Low: 0 };
  (discoveredAddresses || []).forEach((node) => {
    const level = (node?.risk?.risk_level || 'Low');
    if (level in dist) dist[level] += 1;
  });
  return [
    { name: "Critical", value: dist.Critical, color: "#ef4444" },
    { name: "High", value: dist.High, color: "#f43f5e" },
    { name: "Medium", value: dist.Medium, color: "#f59e0b" },
    { name: "Low", value: dist.Low, color: "#10b981" }
  ];
}

export function deriveDashboardMetrics(traceResponse, storedHistory = []) {
  const historyList = Array.isArray(storedHistory) ? storedHistory : [];

  if (!traceResponse || typeof traceResponse !== 'object') {
    if (historyList.length > 0) {
      const highRiskCases = historyList.filter(
        c => c.risk_level === 'Critical' || c.risk_level === 'High'
      ).length;

      const riskCounts = { Critical: 0, High: 0, Medium: 0, Low: 0 };
      historyList.forEach(c => {
        const lvl = c.risk_level || 'Low';
        if (lvl in riskCounts) riskCounts[lvl] += 1;
      });

      return {
        ...EMPTY_DASHBOARD_METRICS,
        total_investigations: historyList.length,
        active_investigations: 0,
        high_risk_wallets: highRiskCases,
        risk_distribution: [
          { name: "Critical", value: riskCounts.Critical, color: "#ef4444" },
          { name: "High", value: riskCounts.High, color: "#f43f5e" },
          { name: "Medium", value: riskCounts.Medium, color: "#f59e0b" },
          { name: "Low", value: riskCounts.Low, color: "#10b981" }
        ],
        recent_investigations: historyList.slice(0, 5).map(c => ({
          id: c.case_id,
          address: c.target_address,
          risk: c.risk_level,
          score: c.risk_score,
          entity: c.entity || 'Unknown',
          hops: c.max_hops,
          date: c.created_at ? c.created_at.slice(0, 10) : ''
        }))
      };
    }
    return { ...EMPTY_DASHBOARD_METRICS };
  }

  const traceResults = traceResponse.trace_results || {};
  const patterns = traceResponse.patterns || {};
  const discoveredAddresses = traceResults.discovered_addresses || [];

  const highRiskCount = discoveredAddresses.filter((node) => {
    const level = node?.risk?.risk_level;
    return level === 'Critical' || level === 'High';
  }).length;

  const attributedCount = discoveredAddresses.filter((node) => {
    return node && node.entity && node.entity !== 'Unknown' && node.entity_type !== 'Unknown';
  }).length;

  const patternSummary = patterns.summary || {};
  const patternCount = patternSummary.total_patterns_detected || 0;
  const patternLabels = [];
  if (patternSummary.has_fan_out) patternLabels.push('Splitting (Fan-Out)');
  if (patternSummary.has_fan_in) patternLabels.push('Consolidation (Fan-In)');
  if (patternSummary.has_rapid_hopping) patternLabels.push('Rapid Hopping');
  if (patternSummary.has_layering) patternLabels.push('Multi-hop Layering');

  const overallRisk = traceResults.overall_risk || {};
  const highestRiskLevel = overallRisk.risk_level || 'Low';
  const highestRiskScore = overallRisk.score || 0;

  const targetNode = discoveredAddresses.find(
    (n) => (n.address || '').toLowerCase() === (traceResponse.target_address || '').toLowerCase()
  ) || discoveredAddresses[0];

  const recentList = historyList.length > 0
    ? historyList.slice(0, 5).map(c => ({
        id: c.case_id,
        address: c.target_address,
        risk: c.risk_level,
        score: c.risk_score,
        entity: c.entity || 'Unknown',
        hops: c.max_hops,
        date: c.created_at ? c.created_at.slice(0, 10) : ''
      }))
    : (targetNode ? [{
        id: 'CASE-CURRENT',
        address: targetNode.address,
        risk: targetNode.risk?.risk_level || highestRiskLevel,
        score: targetNode.risk?.score || highestRiskScore,
        entity: targetNode.entity || 'Unknown',
        hops: targetNode.hop_distance ?? 0,
        date: new Date().toISOString().slice(0, 10)
      }] : []);

  return {
    total_investigations: Math.max(historyList.length, 1),
    active_investigations: 1,
    high_risk_wallets: highRiskCount,
    known_entities_count: attributedCount,
    obfuscation_patterns_count: patternCount,
    risk_distribution: buildRiskDistribution(discoveredAddresses),
    asset_breakdown: buildAssetBreakdown(traceResponse.graph || {}),
    recent_investigations: recentList,
    highest_risk_level: highestRiskLevel,
    highest_risk_score: highestRiskScore,
    obfuscation_pattern_labels: patternLabels
  };
}