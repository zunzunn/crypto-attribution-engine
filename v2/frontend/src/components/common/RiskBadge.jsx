import React from 'react';
import { ShieldAlert, AlertTriangle, AlertCircle, ShieldCheck } from 'lucide-react';
import { getRiskBadgeStyle } from '../../utils/formatters';

export default function RiskBadge({ level = 'Low', score = null, size = 'sm', showIcon = true }) {
  const normalizedLevel = (level || 'Low').toUpperCase();

  const getIcon = () => {
    switch (normalizedLevel) {
      case 'CRITICAL':
        return <ShieldAlert className={size === 'xs' ? 'w-3 h-3' : 'w-3.5 h-3.5'} />;
      case 'HIGH':
        return <AlertTriangle className={size === 'xs' ? 'w-3 h-3' : 'w-3.5 h-3.5'} />;
      case 'MEDIUM':
        return <AlertCircle className={size === 'xs' ? 'w-3 h-3' : 'w-3.5 h-3.5'} />;
      case 'LOW':
      default:
        return <ShieldCheck className={size === 'xs' ? 'w-3 h-3' : 'w-3.5 h-3.5'} />;
    }
  };

  const sizeClass = size === 'xs'
    ? 'text-[10px] px-1.5 py-0.5 gap-1'
    : size === 'lg'
    ? 'text-xs px-3 py-1 gap-1.5 font-bold'
    : 'text-[11px] px-2 py-0.5 gap-1.5 font-semibold';

  return (
    <span
      className={`inline-flex items-center rounded-md border font-mono uppercase tracking-wider ${getRiskBadgeStyle(level)} ${sizeClass}`}
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
