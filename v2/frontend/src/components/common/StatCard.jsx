import React, { useEffect, useState } from 'react';

export default function StatCard({
  label,
  value,
  subtext,
  icon: Icon,
  variant = 'cyan', // 'cyan', 'red', 'blue', 'amber', 'emerald', 'slate'
  badge = null,
  onClick = null
}) {
  const [prevValue, setPrevValue] = useState(value);
  const [isBumping, setIsBumping] = useState(false);

  useEffect(() => {
    if (value !== prevValue) {
      setPrevValue(value);
      setIsBumping(true);
      const timer = setTimeout(() => setIsBumping(false), 600);
      return () => clearTimeout(timer);
    }
  }, [value, prevValue]);

  const colorVariants = {
    cyan: {
      iconBg: 'bg-cyan-500/10 text-cyan-400 border-cyan-500/25',
      glow: 'hover:border-cyan-500/40 hover:shadow-cyan-950/40',
      valueColor: 'text-white'
    },
    red: {
      iconBg: 'bg-red-500/10 text-red-400 border-red-500/25',
      glow: 'hover:border-red-500/40 hover:shadow-red-950/40',
      valueColor: 'text-red-400'
    },
    blue: {
      iconBg: 'bg-blue-500/10 text-blue-400 border-blue-500/25',
      glow: 'hover:border-blue-500/40 hover:shadow-blue-950/40',
      valueColor: 'text-blue-400'
    },
    amber: {
      iconBg: 'bg-amber-500/10 text-amber-400 border-amber-500/25',
      glow: 'hover:border-amber-500/40 hover:shadow-amber-950/40',
      valueColor: 'text-amber-400'
    },
    emerald: {
      iconBg: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/25',
      glow: 'hover:border-emerald-500/40 hover:shadow-emerald-950/40',
      valueColor: 'text-emerald-400'
    },
    slate: {
      iconBg: 'bg-slate-800/60 text-slate-300 border-slate-700/50',
      glow: 'hover:border-slate-600 hover:shadow-slate-900/40',
      valueColor: 'text-slate-200'
    }
  };

  const currentVariant = colorVariants[variant] || colorVariants.cyan;

  return (
    <div
      onClick={onClick}
      className={`cyber-card rounded-xl p-5 border border-slate-800/80 flex flex-col justify-between transition-all duration-300 ${
        onClick ? 'cursor-pointer' : 'cursor-default'
      } ${currentVariant.glow}`}
    >
      <div className="flex items-start justify-between">
        <div>
          <span className="text-xs text-slate-400 font-medium tracking-wide uppercase">{label}</span>
          <div className="flex items-baseline gap-2 mt-1.5">
            <h4
              className={`text-2xl sm:text-3xl font-bold font-mono tracking-tight transition-transform duration-300 ${
                currentVariant.valueColor
              } ${isBumping ? 'scale-110 text-cyan-300' : 'scale-100'}`}
            >
              {value}
            </h4>
            {badge && (
              <span className="text-[10px] px-1.5 py-0.5 rounded font-mono font-medium bg-slate-800/80 text-slate-300 border border-slate-700/60">
                {badge}
              </span>
            )}
          </div>
        </div>

        {Icon && (
          <div className={`p-3 rounded-xl border ${currentVariant.iconBg} shadow-sm`}>
            <Icon className="w-5 h-5" />
          </div>
        )}
      </div>

      {subtext && (
        <div className="mt-3 pt-2.5 border-t border-slate-800/60 flex items-center justify-between text-[11px] text-slate-400">
          <span className="truncate">{subtext}</span>
        </div>
      )}
    </div>
  );
}
