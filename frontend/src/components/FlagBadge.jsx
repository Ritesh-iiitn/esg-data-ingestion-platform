import React from 'react';

const FLAG_STYLES = {
  UNIT_MISMATCH: { bg: 'bg-yellow-500/10 text-yellow-400 border-yellow-500/20', label: 'Unit Mismatch' },
  OUTLIER: { bg: 'bg-orange-500/10 text-orange-400 border-orange-500/20', label: 'Outlier' },
  MISSING_FACTOR: { bg: 'bg-red-500/10 text-red-400 border-red-500/20', label: 'Missing Factor' },
  DATE_GAP: { bg: 'bg-blue-500/10 text-blue-400 border-blue-500/20', label: 'Date Gap' },
  DUPLICATE: { bg: 'bg-purple-500/10 text-purple-400 border-purple-500/20', label: 'Duplicate' },
  ZERO_VALUE: { bg: 'bg-teal-500/10 text-teal-400 border-teal-500/20', label: 'Zero Value' }
};

export default function FlagBadge({ type, message }) {
  const style = FLAG_STYLES[type] || { bg: 'bg-slate-500/10 text-slate-400 border-slate-500/20', label: type };
  
  return (
    <div className="relative group inline-block">
      <span className={`px-2 py-0.5 text-xs font-semibold rounded-full border ${style.bg} cursor-pointer`}>
        {style.label}
      </span>
      {message && (
        <div className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 hidden group-hover:block w-48 p-2 text-xs bg-slate-950 text-slate-200 border border-slate-800 rounded shadow-xl z-20 pointer-events-none">
          {message}
          <div className="absolute top-full left-1/2 transform -translate-x-1/2 -mt-1 border-4 border-transparent border-t-slate-950"></div>
        </div>
      )}
    </div>
  );
}
