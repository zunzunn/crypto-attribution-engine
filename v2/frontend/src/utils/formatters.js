/**
 * Forensic formatting utilities for Crypto Attribution Engine
 */

export function shortenAddress(address = '', startChars = 6, endChars = 4) {
  if (!address) return '';
  if (address.length <= startChars + endChars) return address;
  return `${address.substring(0, startChars)}...${address.substring(address.length - endChars)}`;
}

export function formatAmount(amount, symbol = 'ETH') {
  const num = parseFloat(amount);
  if (isNaN(num)) return `0.00 ${symbol}`;
  return `${num.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 4 })} ${symbol}`;
}

export function formatNumber(num) {
  if (num === null || num === undefined || isNaN(num)) return '0';
  return Number(num).toLocaleString();
}

export function formatTimestamp(ts) {
  if (!ts) return 'N/A';
  try {
    const d = typeof ts === 'number' ? (ts > 1e11 ? new Date(ts) : new Date(ts * 1000)) : new Date(ts);
    return d.toLocaleString('en-US', {
      year: 'numeric',
      month: 'short',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      hour12: false
    });
  } catch {
    return String(ts);
  }
}

export function isValidEthAddress(address) {
  if (!address || typeof address !== 'string') return false;
  return /^0x[a-fA-F0-9]{40}$/.test(address.trim());
}

export function generateCaseId(targetAddress = '') {
  const dateStr = new Date().toISOString().slice(0, 10).replace(/-/g, '');
  const suffix = targetAddress ? targetAddress.slice(2, 6).toUpperCase() : Math.random().toString(36).substring(2, 6).toUpperCase();
  return `CASE-${dateStr}-${suffix}`;
}

export function getRiskBadgeStyle(riskLevel = 'Low') {
  switch ((riskLevel || '').toUpperCase()) {
    case 'CRITICAL':
      return 'bg-red-500/15 text-red-400 border-red-500/30 shadow-red-950/20';
    case 'HIGH':
      return 'bg-rose-500/15 text-rose-400 border-rose-500/30 shadow-rose-950/20';
    case 'MEDIUM':
      return 'bg-amber-500/15 text-amber-400 border-amber-500/30 shadow-amber-950/20';
    case 'LOW':
    default:
      return 'bg-emerald-500/15 text-emerald-400 border-emerald-500/30 shadow-emerald-950/20';
  }
}

export function getRiskColor(riskLevel = 'Low') {
  switch ((riskLevel || '').toUpperCase()) {
    case 'CRITICAL':
      return '#ef4444';
    case 'HIGH':
      return '#f43f5e';
    case 'MEDIUM':
      return '#f59e0b';
    case 'LOW':
    default:
      return '#10b981';
  }
}

export function getEntityBadgeStyle(entityType = 'Unknown') {
  const t = (entityType || 'Unknown').toUpperCase();
  if (t.includes('MIXER')) {
    return 'bg-red-500/15 text-red-400 border-red-500/30';
  }
  if (t.includes('VASP') || t.includes('EXCHANGE')) {
    return 'bg-blue-500/15 text-blue-400 border-blue-500/30';
  }
  if (t.includes('BRIDGE')) {
    return 'bg-amber-500/15 text-amber-400 border-amber-500/30';
  }
  if (t.includes('SCAM') || t.includes('FRAUD') || t.includes('PHISHING')) {
    return 'bg-purple-500/15 text-purple-400 border-purple-500/30';
  }
  return 'bg-slate-700/30 text-slate-400 border-slate-700/50';
}

export function getEntityColor(entityType = 'Unknown') {
  const t = (entityType || 'Unknown').toUpperCase();
  if (t.includes('MIXER')) return '#ef4444';
  if (t.includes('VASP') || t.includes('EXCHANGE')) return '#3b82f6';
  if (t.includes('BRIDGE')) return '#f59e0b';
  if (t.includes('SCAM') || t.includes('FRAUD') || t.includes('PHISHING')) return '#a855f7';
  return '#64748b';
}
