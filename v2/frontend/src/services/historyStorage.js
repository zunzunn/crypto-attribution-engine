/**
 * Case Management & Investigation History Storage Service
 */

const STORAGE_KEY = 'cae_investigation_cases_v2';

export function getStoredHistory() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw);
    return Array.isArray(parsed) ? parsed : [];
  } catch (err) {
    console.error('Failed to load investigation history from localStorage', err);
    return [];
  }
}

export function saveInvestigation({ targetAddress, traceResponse, isLive = false, maxHops = 2, caseId = null }) {
  if (!targetAddress || !traceResponse) return null;

  try {
    const history = getStoredHistory();
    const discovered = traceResponse.trace_results?.discovered_addresses || [];
    const targetNode = discovered.find(
      (n) => (n.address || '').toLowerCase() === targetAddress.toLowerCase()
    ) || discovered[0] || {};

    const overallRisk = traceResponse.trace_results?.overall_risk || {};
    const riskLevel = overallRisk.risk_level || targetNode.risk?.risk_level || 'Low';
    const riskScore = overallRisk.score ?? targetNode.risk?.score ?? 0;

    const id = caseId || `CASE-${Date.now().toString(36).toUpperCase().slice(-6)}`;
    const now = new Date().toISOString();

    const newCase = {
      case_id: id,
      target_address: targetAddress,
      created_at: now,
      risk_level: riskLevel,
      risk_score: riskScore,
      entity: targetNode.entity || 'Unknown',
      discovered_count: discovered.length,
      max_hops: maxHops,
      is_live: Boolean(isLive),
      trace_response: traceResponse,
    };

    // Replace if same target or add to top
    const existingIndex = history.findIndex(
      (item) => item.target_address.toLowerCase() === targetAddress.toLowerCase()
    );

    let updatedHistory;
    if (existingIndex >= 0) {
      updatedHistory = [newCase, ...history.filter((_, idx) => idx !== existingIndex)];
    } else {
      updatedHistory = [newCase, ...history].slice(0, 50); // cap at 50 cases
    }

    localStorage.setItem(STORAGE_KEY, JSON.stringify(updatedHistory));
    return newCase;
  } catch (err) {
    console.error('Failed to save investigation to localStorage', err);
    return null;
  }
}

export function removeInvestigation(caseId) {
  try {
    const history = getStoredHistory();
    const filtered = history.filter((item) => item.case_id !== caseId);
    localStorage.setItem(STORAGE_KEY, JSON.stringify(filtered));
    return filtered;
  } catch (err) {
    console.error('Failed to delete investigation from localStorage', err);
    return getStoredHistory();
  }
}

export function clearAllInvestigations() {
  try {
    localStorage.removeItem(STORAGE_KEY);
    return [];
  } catch (err) {
    console.error('Failed to clear investigation history', err);
    return [];
  }
}

export function getInvestigationById(caseId) {
  const history = getStoredHistory();
  return history.find((c) => c.case_id === caseId) || null;
}
