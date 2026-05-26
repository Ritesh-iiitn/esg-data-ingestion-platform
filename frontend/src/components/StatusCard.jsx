import React from 'react';

const COLORS = {
  emerald: {
    bg: 'custom-card-emerald',
    text: 'text-emerald-600',
    border: 'border-emerald-200/60',
    glow: 'shadow-emerald-500/5'
  },
  amber: {
    bg: 'custom-card-amber',
    text: 'text-amber-600',
    border: 'border-amber-200/60',
    glow: 'shadow-amber-500/5'
  },
  red: {
    bg: 'custom-card-red',
    text: 'text-red-600',
    border: 'border-red-200/60',
    glow: 'shadow-red-500/5'
  },
  indigo: {
    bg: 'custom-card-indigo',
    text: 'text-indigo-600',
    border: 'border-indigo-200/60',
    glow: 'shadow-indigo-500/5'
  },
  rose: {
    bg: 'custom-card-rose',
    text: 'text-rose-600',
    border: 'border-rose-200/60',
    glow: 'shadow-rose-500/5'
  },
  slate: {
    bg: 'custom-card-slate',
    text: 'text-slate-600',
    border: 'border-slate-200/60',
    glow: 'shadow-slate-500/5'
  }
};

export default function StatusCard({ title, value, icon: Icon, color = 'slate', subtitle }) {
  const styles = COLORS[color] || COLORS.slate;
  
  const ACCENTS = {
    emerald: 'border-l-brand',
    indigo: 'border-l-pending',
    amber: 'border-l-flagged',
    red: 'border-l-rejected',
    rose: 'border-l-brand',
    slate: 'border-l-slate'
  };
  const accentClass = ACCENTS[color] || '';
  
  return (
    <div className={`glass bg-gradient-to-br ${styles.bg} border ${styles.border} ${accentClass} ${styles.glow} p-5 rounded-2xl shadow-lg relative overflow-hidden transition-all duration-300 hover:scale-[1.02] hover:shadow-xl`}>
      <div className="flex justify-between items-start">
        <div>
          <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">{title}</span>
          <h3 className="text-2xl font-bold mt-2 text-slate-100">{value}</h3>
          {subtitle && <p className="text-xs text-slate-500 mt-1">{subtitle}</p>}
        </div>
        <div className={`p-3 rounded-xl bg-slate-900 border border-slate-800 ${styles.text}`}>
          {Icon && <Icon className="w-6 h-6" />}
        </div>
      </div>
      <div className={`absolute -bottom-8 -left-8 w-24 h-24 rounded-full filter blur-3xl opacity-10 bg-current ${styles.text}`}></div>
    </div>
  );
}
