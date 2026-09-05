import React from 'react';
import { ShieldAlert, AlertTriangle, AlertCircle, ShieldCheck } from 'lucide-react';

export default function RiskBadge({ level = 'Low', score = null, size = 'sm', showIcon = true }) {
  const normalizedLevel = (level || 'Low').toUpperCase();

  const getRiskStyle = () => {
    switch (normalizedLevel) {
      case 'CRITICAL':
        return { bg: 'bg-rose-500/15', text: 'text-rose-400', border: 'border-rose-500/30' };
      case 'HIGH':
        return { bg: 'bg-rose-500/15', text: 'text-rose-400', border: 'border-rose-500/30' };
      case 'MEDIUM':
        return { bg: 'bg-amber-500/15', text: 'text-amber-400', border: 'border-amber-500/30' };
      case 'LOW':
      default:
        return { bg: 'bg-emerald-500/15', text: 'text-emerald-400', border: 'border-emerald-500/30' };
    }
  };

  const style = getRiskStyle();

  const getIcon = () => {
    const iconClass = size === 'xs' ? 'w-2.5 h-2.5' : 'w-3 h-3';
    switch (normalizedLevel) {
      case 'CRITICAL':
        return <ShieldAlert className={iconClass} />;
      case 'HIGH':
        return <AlertTriangle className={iconClass} />;
      case 'MEDIUM':
        return <AlertCircle className={iconClass} />;
      case 'LOW':
      default:
        return <ShieldCheck className={iconClass} />;
    }
  };

  const sizeClass = size === 'xs'
    ? 'text-[8px] px-1.5 py-0.5 gap-1'
    : size === 'lg'
    ? 'text-xs px-2.5 py-1 gap-1.5 font-bold'
    : 'text-[9px] px-2 py-0.5 gap-1 font-medium';

  return (
    <span
      className={`inline-flex items-center rounded-md border font-medium uppercase tracking-wider ${style.bg} ${style.text} ${style.border} ${sizeClass}`}
    >
      {showIcon && getIcon()}
      <span>{level}</span>
      {score !== null && score !== undefined && (
        <span className="opacity-75 font-normal ml-0.5">
          ({typeof score === 'number' ? score.toFixed(1) : score})
        </span>
      )}
    </span>
  );
}