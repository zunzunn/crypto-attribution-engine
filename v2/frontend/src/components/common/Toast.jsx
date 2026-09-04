import React, { useEffect } from 'react';
import { CheckCircle2, AlertTriangle, XCircle, Info, X } from 'lucide-react';

export default function Toast({ toasts = [], onDismiss }) {
  if (!toasts || toasts.length === 0) return null;

  return (
    <div className="fixed bottom-5 right-5 z-50 flex flex-col gap-2 pointer-events-none max-w-sm w-full">
      {toasts.map((toast) => (
        <ToastItem key={toast.id} toast={toast} onDismiss={onDismiss} />
      ))}
    </div>
  );
}

function ToastItem({ toast, onDismiss }) {
  useEffect(() => {
    const timer = setTimeout(() => {
      onDismiss(toast.id);
    }, toast.duration || 3500);
    return () => clearTimeout(timer);
  }, [toast, onDismiss]);

  const typeStyles = {
    success: {
      border: 'border-emerald-500/40',
      bg: 'bg-slate-900/95',
      icon: <CheckCircle2 className="w-4 h-4 text-emerald-400 flex-shrink-0" />,
      text: 'text-emerald-200'
    },
    error: {
      border: 'border-red-500/40',
      bg: 'bg-slate-900/95',
      icon: <XCircle className="w-4 h-4 text-red-400 flex-shrink-0" />,
      text: 'text-red-200'
    },
    warning: {
      border: 'border-amber-500/40',
      bg: 'bg-slate-900/95',
      icon: <AlertTriangle className="w-4 h-4 text-amber-400 flex-shrink-0" />,
      text: 'text-amber-200'
    },
    info: {
      border: 'border-cyan-500/40',
      bg: 'bg-slate-900/95',
      icon: <Info className="w-4 h-4 text-cyan-400 flex-shrink-0" />,
      text: 'text-cyan-200'
    }
  };

  const style = typeStyles[toast.type] || typeStyles.info;

  return (
    <div
      className={`pointer-events-auto flex items-center justify-between gap-3 px-4 py-3 rounded-xl border ${style.border} ${style.bg} backdrop-blur-md shadow-xl transition-all duration-300 animate-slide-in text-xs`}
    >
      <div className="flex items-center gap-2.5">
        {style.icon}
        <span className={`${style.text} font-medium leading-tight`}>{toast.message}</span>
      </div>
      <button
        onClick={() => onDismiss(toast.id)}
        className="text-slate-400 hover:text-white p-1 transition"
      >
        <X className="w-3.5 h-3.5" />
      </button>
    </div>
  );
}
