import axios from 'axios';
import { MOCK_TRACE_DATA, MOCK_DASHBOARD_METRICS } from './mockData';

const API_BASE_URL = 'http://127.0.0.1:8000';

const client = axios.create({
  baseURL: API_BASE_URL,
  timeout: 8000,
  headers: {
    'Content-Type': 'application/json'
  }
});

export async function checkApiHealth() {
  try {
    const res = await client.get('/');
    return { isLive: true, data: res.data };
  } catch (err) {
    return { isLive: false, data: null };
  }
}

export async function fetchAddressTrace(targetAddress, maxHops = 2, useEtherscan = false) {
  try {
    const res = await client.post('/api/v2/trace', {
      target_address: targetAddress,
      max_hops: maxHops,
      use_etherscan: useEtherscan
    });
    return { isLive: true, data: res.data };
  } catch (err) {
    console.warn("Backend API offline or unreachable. Using fallback mock trace dataset.", err.message);
    // Return mock data with target_address substituted
    const fallbackData = { ...MOCK_TRACE_DATA, target_address: targetAddress };
    return { isLive: false, data: fallbackData };
  }
}

export async function lookupAddressIntelligence(address) {
  try {
    const res = await client.get(`/api/v2/address/${address}`);
    return { isLive: true, data: res.data };
  } catch (err) {
    // Find address in mock data or construct synthetic unknown response
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

export async function fetchInvestigationReport(targetAddress, traceResults, patterns) {
  try {
    const res = await client.post('/api/v2/report', {
      target_address: targetAddress,
      trace_results: traceResults,
      patterns: patterns,
      network: "Ethereum Mainnet"
    });
    return { isLive: true, data: res.data };
  } catch (err) {
    return {
      isLive: false,
      data: {
        json_report: {
          case_metadata: { case_id: "CASE-MOCK-2026", target_address: targetAddress, network: "Ethereum Mainnet", generated_at: new Date().toISOString() },
          investigation_summary: MOCK_TRACE_DATA.report_summary,
          attributed_entities: MOCK_TRACE_DATA.trace_results.discovered_addresses.filter(n => n.entity !== "Unknown"),
          detected_behavioral_patterns: MOCK_TRACE_DATA.patterns,
          disclaimer: "Investigative priority report derived from fallback mock environment."
        },
        markdown_report: `# Crypto Attribution & Forensic Investigation Report\n\n**Case ID:** \`CASE-MOCK-2026\`\n**Target Address:** \`${targetAddress}\`\n\n## Summary\n- Total Traced: ${MOCK_TRACE_DATA.report_summary.total_addresses_traced}\n- Max Hops: ${MOCK_TRACE_DATA.report_summary.maximum_hop_distance}\n- Highest Risk: **${MOCK_TRACE_DATA.report_summary.highest_risk_level}** (${MOCK_TRACE_DATA.report_summary.highest_risk_score}/100)`
      }
    };
  }
}

export function getDashboardMetrics() {
  return MOCK_DASHBOARD_METRICS;
}
