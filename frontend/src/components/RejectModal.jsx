import React, { useState, useEffect } from 'react';
import { X, AlertTriangle } from 'lucide-react';

export default function RejectModal({ isOpen, onClose, onConfirm, recordId }) {
  console.log('RejectModal evaluated in DOM! Prop isOpen:', isOpen, 'Prop recordId:', recordId);
  const [note, setNote] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (isOpen) {
      setNote('');
      setError('');
    }
  }, [isOpen]);

  if (!isOpen) return null;

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!note.trim()) {
      setError('A justification note is required to reject a record.');
      return;
    }
    
    setLoading(true);
    setError('');
    
    try {
      await onConfirm(recordId, note);
      setNote('');
      onClose();
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to reject the record.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="custom-modal-backdrop">
      <div className="custom-modal-card">
        <div className="flex justify-between items-center p-5 border-b border-slate-800">
          <div className="flex items-center gap-2 text-rose-400">
            <AlertTriangle className="w-5 h-5" />
            <h3 className="font-bold text-slate-100">Reject Emission Record</h3>
          </div>
          <button onClick={onClose} className="text-slate-400 hover:text-slate-200">
            <X className="w-5 h-5" />
          </button>
        </div>
        
        <form onSubmit={handleSubmit} className="p-5">
          <p className="text-xs text-slate-400 mb-4">
            Rejecting this record will flag it as <span className="text-rose-400 font-semibold">REJECTED</span>. You must provide an audit note explaining the rejection reason (e.g. data correction required).
          </p>
          
          <div className="mb-4">
            <label className="block text-xs font-semibold text-slate-300 mb-2 uppercase tracking-wide">
              Rejection Note / Justification
            </label>
            <textarea
              value={note}
              onChange={(e) => setNote(e.target.value)}
              placeholder="e.g. Utility bill date overlap detected, or fuel quantity outlier needs manual audit verify."
              className="w-full h-24 px-3 py-2 text-sm bg-slate-950 border border-slate-800 rounded-xl focus:border-rose-500 focus:outline-none text-slate-200 placeholder-slate-600 resize-none"
              required
            />
          </div>

          {error && (
            <p className="text-xs text-rose-400 mb-4 bg-rose-500/10 border border-rose-500/20 p-2.5 rounded-lg">
              {error}
            </p>
          )}

          <div className="flex justify-end gap-3">
            <button
              type="button"
              onClick={onClose}
              disabled={loading}
              className="px-4 py-2 text-sm font-semibold text-slate-400 hover:text-slate-200 bg-slate-850 hover:bg-slate-800 rounded-xl"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading}
              className="px-4 py-2 text-sm font-bold text-slate-950 bg-rose-500 hover:bg-rose-600 rounded-xl flex items-center justify-center gap-1 shadow-lg shadow-rose-500/20"
            >
              {loading ? 'Processing...' : 'Confirm Rejection'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
