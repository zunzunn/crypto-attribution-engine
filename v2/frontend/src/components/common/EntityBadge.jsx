import React from 'react';
import { Building2, Shuffle, ArrowRightLeft, Skull, HelpCircle, Coins } from 'lucide-react';
import { getEntityBadgeStyle } from '../../utils/formatters';

export default function EntityBadge({ type = 'Unknown', size = 'sm', showIcon = true }) {
  const t = (type || 'Unknown').toUpperCase();

  const getIcon = () => {
    if (t.includes('MIXER')) return <Shuffle className={size === 'xs' ? 'w-2.5 h-2.5' : 'w-3 h-3'} />;
    if (t.includes('VASP') || t.includes('EXCHANGE')) return <Building2 className={size === 'xs' ? 'w-2.5 h-2.5' : 'w-3 h-3'} />;
    if (t.includes('BRIDGE')) return <ArrowRightLeft className={size === 'xs' ? 'w-2.5 h-2.5' : 'w-3 h-3'} />;
    if (t.includes('SCAM') || t.includes('FRAUD') || t.includes('PHISHING')) return <Skull className={size === 'xs' ? 'w-2.5 h-2.5' : 'w-3 h-3'} />;
    if (t.includes('TOKEN')) return <Coins className={size === 'xs' ? 'w-2.5 h-2.5' : 'w-3 h-3'} />;
    return <HelpCircle className={size === 'xs' ? 'w-2.5 h-2.5' : 'w-3 h-3'} />;
  };

  const sizeClass = size === 'xs'
    ? 'text-[10px] px-1.5 py-0.5 gap-1'
    : size === 'lg'
    ? 'text-xs px-2.5 py-1 gap-1.5 font-bold'
    : 'text-[11px] px-2 py-0.5 gap-1 font-medium';

  return (
    <span className={`inline-flex items-center rounded border ${getEntityBadgeStyle(type)} ${sizeClass}`}>
      {showIcon && getIcon()}
      <span>{type}</span>
    </span>
  );
}
