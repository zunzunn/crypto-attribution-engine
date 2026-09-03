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

export function getRiskBadgeStyle(riskLevel = 'Low') {
  switch (riskLevel.toUpperCase()) {
    case 'CRITICAL':
      return 'bg-red-950/80 text-red-400 border-red-800/80 shadow-red-900/30';
    case 'HIGH':
      return 'bg-rose-950/80 text-rose-400 border-rose-800/80 shadow-rose-900/30';
    case 'MEDIUM':
      return 'bg-amber-950/80 text-amber-400 border-amber-800/80 shadow-amber-900/30';
    case 'LOW':
    default:
      return 'bg-emerald-950/80 text-emerald-400 border-emerald-800/80 shadow-emerald-900/30';
  }
}

export function getEntityBadgeStyle(entityType = 'Unknown') {
  switch (entityType.toUpperCase()) {
    case 'MIXER':
      return 'bg-red-500/20 text-red-400 border-red-500/30';
    case 'VASP':
    case 'EXCHANGE':
      return 'bg-blue-500/20 text-blue-400 border-blue-500/30';
    case 'BRIDGE':
      return 'bg-amber-500/20 text-amber-400 border-amber-500/30';
    case 'SCAM':
    case 'FRAUD':
      return 'bg-purple-500/20 text-purple-400 border-purple-500/30';
    case 'UNKNOWN':
    default:
      return 'bg-slate-500/20 text-slate-400 border-slate-500/30';
  }
}
