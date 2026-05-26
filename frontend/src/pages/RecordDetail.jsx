import React, { useState, useEffect } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import client from '../api/client';
import FlagBadge from '../components/FlagBadge';
import RejectModal from '../components/RejectModal';
import { 
  ArrowLeft, Calendar, User, FileText, Activity, ShieldAlert,
  ArrowRight, ShieldCheck, CheckCircle2, XOctagon, Loader2
} from 'lucide-react';

export default function RecordDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [record, setRecord] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  // Rejection modal
  const [isRejectOpen, setIsRejectOpen] = useState(false);

  const fetchRecordDetails = async () => {
    try {
      const res = await client.get(`/records/${id}/`);
      setRecord(res.data);
    } catch (err) {
      setError(err.response?.data?.error || 'Record not found.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRecordDetails();
  }, [id]);

  const handleApprove = async () => {
    try {
      await client.post(`/records/${id}/approve/`);
      fetchRecordDetails();
    } catch (err) {
      alert('Approval failed: ' + (err.response?.data?.error || err.message));
    }
  };

  const handleRejectConfirm = async (rid, note) => {
    await client.post(`/records/${rid}/reject/`, { note });
    fetchRecordDetails();
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-[500px]">
        <Loader2 className="w-10 h-10 animate-spin text-brand-400" />
      </div>
    );
  }

  if (error || !record) {
    return (
      <div className="glass p-8 text-center max-w-md mx-auto rounded-2xl border border-red-500/20 mt-12">
        <h3 className="text-xl font-bold text-red-400 mb-2">Error Loading Record</h3>
        <p className="text-sm text-slate-400 mb-6">{error || 'The requested emission record could not be found.'}</p>
        <Link to="/dashboard" className="px-5 py-2.5 bg-slate-900 border border-slate-800 rounded-xl text-xs text-slate-200 hover:text-slate-100">
          Return to Dashboard
        </Link>
      </div>
    );
  }

  const isApproved = record?.status === 'APPROVED';
  const isRejected = record?.status === 'REJECTED';
  const isFlagged = record?.status === 'FLAGGED';

  const co2eKg = record?.co2e_kg || 0;
  const rawValue = record?.raw_value || 0;
  const normalizedValue = record?.normalized_value || 0;
  const emissionFactor = record?.emission_factor || 0;

  return (
    <div className="space-y-8 max-w-6xl mx-auto">
      {/* Back button & Action Header */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 pb-4 border-b border-slate-850">
        <Link to="/dashboard" className="inline-flex items-center gap-2 text-xs font-semibold text-slate-400 hover:text-slate-200 transition-colors">
          <ArrowLeft className="w-4 h-4" /> Back to Dashboard
        </Link>
        
        <div className="flex gap-3">
          {isApproved ? (
            <div className="px-4 py-2 bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 rounded-xl text-xs font-bold flex items-center gap-1.5 shadow-lg shadow-emerald-500/5">
              <CheckCircle2 className="w-4 h-4" /> Approved & Locked
            </div>
          ) : (
            <>
              <button
                onClick={handleApprove}
                className="px-5 py-2 bg-emerald-500 hover:bg-emerald-600 text-slate-950 font-bold rounded-xl text-xs flex items-center gap-1.5 shadow-lg shadow-emerald-500/20 transition-all"
              >
                Approve Emission Record
              </button>
              <button
                onClick={() => setIsRejectOpen(true)}
                className="px-5 py-2 bg-rose-500/10 hover:bg-rose-500 text-rose-400 hover:text-slate-950 border border-rose-500/20 rounded-xl text-xs flex items-center gap-1.5 transition-all"
              >
                Reject Record
              </button>
            </>
          )}
        </div>
      </div>

      {/* Basic metadata box */}
      <div className="glass p-6 rounded-2xl bg-gradient-to-br from-slate-900/60 to-slate-900/20 border border-slate-850 grid grid-cols-1 md:grid-cols-4 gap-6">
        <div>
          <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider block">Source type</span>
          <span className={`inline-block px-2.5 py-0.5 rounded font-bold uppercase tracking-wider text-[10px] mt-1.5 ${
            record.source_type === 'SAP' ? 'bg-blue-500/10 text-blue-400' : record.source_type === 'UTILITY' ? 'bg-indigo-500/10 text-indigo-400' : 'bg-rose-500/10 text-rose-400'
          }`}>
            {record.source_type} (Scope {record.scope})
          </span>
        </div>
        
        <div>
          <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider block">Activity Type</span>
          <span className="font-bold text-slate-200 capitalize mt-1.5 block">{record.activity_type.replace('_', ' ')}</span>
        </div>

        <div>
          <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider block">Date Range / Period</span>
          <span className="text-sm font-semibold text-slate-300 mt-1.5 block flex items-center gap-1">
            <Calendar className="w-4 h-4 text-slate-500" />
            {record.period_start === record.period_end ? (
              <span>{record.period_start}</span>
            ) : (
              <span>{record.period_start} to {record.period_end}</span>
            )}
          </span>
        </div>

        <div>
          <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider block">Calculated Carbon footprint</span>
          <span className="text-xl font-extrabold text-rose-400 mt-1 block font-mono">
            {co2eKg.toLocaleString(undefined, {minimumFractionDigits: 1, maximumFractionDigits: 2})} kg CO2e
            <span className="text-slate-500 text-xs font-normal block">{(co2eKg / 1000).toFixed(4)} tonnes CO2e</span>
          </span>
        </div>
      </div>

      {/* Two Columns: Normalization & Audit Logs vs Raw JSON */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        
        {/* LEFT COLUMN: Normalization Steps & Audit Timeline */}
        <div className="space-y-8">
          
          {/* Normalization breakdown */}
          <div className="glass p-6 rounded-2xl border border-slate-850 space-y-6">
            <h3 className="text-lg font-bold text-slate-200 flex items-center gap-2 border-b border-slate-850 pb-3">
              <Activity className="w-5 h-5 text-brand-400" /> Normalization Steps & Factors
            </h3>
            
            <div className="space-y-4 text-xs">
              <div className="flex justify-between items-center bg-slate-950/40 p-3 border border-slate-850 rounded-xl">
                <div>
                  <span className="text-slate-400 block font-semibold">Raw Input Value</span>
                  <span className="text-slate-500 block text-[10px] mt-0.5">Exactly as imported</span>
                </div>
                <span className="font-bold text-slate-200 font-mono text-sm">{rawValue.toLocaleString()} {record.raw_unit}</span>
              </div>
              
              <div className="flex justify-between items-center bg-slate-950/40 p-3 border border-slate-850 rounded-xl">
                <div>
                  <span className="text-slate-400 block font-semibold">Normalized Value</span>
                  <span className="text-slate-500 block text-[10px] mt-0.5">Converted to standard unit</span>
                </div>
                <span className="font-bold text-slate-200 font-mono text-sm">{normalizedValue.toLocaleString()} {record.normalized_unit}</span>
              </div>

              <div className="flex justify-between items-center bg-slate-950/40 p-3 border border-slate-850 rounded-xl">
                <div>
                  <span className="text-slate-400 block font-semibold">Emission Factor Mapping</span>
                  <span className="text-slate-500 block text-[10px] mt-0.5">Source: {record.emission_factor_source}</span>
                </div>
                <span className="font-bold text-rose-300 font-mono text-sm">{emissionFactor} kg CO2e / {record.normalized_unit}</span>
              </div>

              {/* Equation flow */}
              <div className="p-4 bg-brand-500/5 border border-brand-500/10 rounded-xl space-y-2">
                <span className="text-[10px] font-bold text-brand-400 uppercase tracking-wide block">Auditable Calculation Formula</span>
                <p className="font-mono text-sm text-brand-300 flex items-center flex-wrap gap-1">
                  <span>{normalizedValue.toLocaleString()}</span>
                  <span className="text-slate-500">({record.normalized_unit})</span>
                  <span className="text-slate-400">×</span>
                  <span>{emissionFactor}</span>
                  <span className="text-slate-500">(kg/unit)</span>
                  <ArrowRight className="w-3.5 h-3.5 mx-1 text-slate-500" />
                  <span className="font-extrabold text-brand-400">{co2eKg.toLocaleString()} kg CO2e</span>
                </p>
              </div>
            </div>
          </div>

          {/* Anomalous Flags */}
          <div className="glass p-6 rounded-2xl border border-slate-850 space-y-4">
            <h3 className="text-lg font-bold text-slate-200 flex items-center gap-2 border-b border-slate-850 pb-3">
              <ShieldAlert className="w-5 h-5 text-amber-400" /> Active Compliance Flags
            </h3>
            
            <div className="space-y-3">
              {record.flags && record.flags.length > 0 ? (
                record.flags.map((f) => (
                  <div key={f.id} className="p-3.5 bg-slate-950/60 border border-slate-850 rounded-xl flex items-start gap-3">
                    <FlagBadge type={f.flag_type} />
                    <div className="space-y-0.5">
                      <span className="text-[10px] text-slate-500 font-semibold block">{new Date(f.created_at).toLocaleString()}</span>
                      <p className="text-xs text-slate-300">{f.message}</p>
                    </div>
                  </div>
                ))
              ) : (
                <div className="text-center py-6 text-xs text-slate-500 flex items-center justify-center gap-2">
                  <ShieldCheck className="w-6 h-6 text-emerald-400" /> No compliance flags found for this record.
                </div>
              )}
            </div>
          </div>
        </div>

        {/* RIGHT COLUMN: Timeline & Raw JSON Data */}
        <div className="space-y-8">
          
          {/* Audit Timeline */}
          <div className="glass p-6 rounded-2xl border border-slate-850 space-y-6">
            <h3 className="text-lg font-bold text-slate-200 flex items-center gap-2 border-b border-slate-850 pb-3">
              <Activity className="w-5 h-5 text-brand-400" /> Audit Log & Lifecycle
            </h3>
            
            <div className="relative pl-6 border-l border-slate-800 space-y-6">
              {record.audit_logs && record.audit_logs.length > 0 ? (
                record.audit_logs.map((log) => {
                  const isLogApprove = log.action === 'APPROVED';
                  const isLogReject = log.action === 'REJECTED';
                  const isLogUpload = log.action === 'UPLOADED';
                  
                  return (
                    <div key={log.id} className="relative">
                      {/* Timeline dot */}
                      <span className={`absolute -left-[31px] top-1 w-3 h-3 rounded-full border-2 ${
                        isLogApprove 
                          ? 'bg-emerald-500 border-slate-900' 
                          : isLogReject 
                          ? 'bg-rose-500 border-slate-900' 
                          : 'bg-slate-500 border-slate-900'
                      }`}></span>
                      
                      <div className="space-y-1">
                        <div className="flex justify-between items-center">
                          <span className={`text-[10px] font-bold uppercase tracking-wider ${
                            isLogApprove ? 'text-emerald-400' : isLogReject ? 'text-rose-400' : 'text-slate-400'
                          }`}>
                            {log.action}
                          </span>
                          <span className="text-[10px] text-slate-500">{new Date(log.performed_at).toLocaleString()}</span>
                        </div>
                        
                        <div className="flex items-center gap-1 text-slate-300 text-xs">
                          <User className="w-3.5 h-3.5 text-slate-500" />
                          <span>{log.performed_by_username || 'System Ingest'}</span>
                        </div>
                        
                        {log.note && (
                          <p className="text-xs text-slate-400 italic bg-slate-950/45 p-2 rounded border border-slate-850 mt-1">
                            "{log.note}"
                          </p>
                        )}
                      </div>
                    </div>
                  );
                })
              ) : (
                <p className="text-xs text-slate-500">No audit history found.</p>
              )}
            </div>
          </div>

          {/* Raw JSON Data block */}
          <div className="glass p-6 rounded-2xl border border-slate-850 space-y-4">
            <h3 className="text-lg font-bold text-slate-200 flex items-center gap-2 border-b border-slate-850 pb-3">
              <FileText className="w-5 h-5 text-indigo-400" /> Raw Imported CSV Data
            </h3>
            
            <div className="p-4 bg-slate-950 border border-slate-850 rounded-xl overflow-x-auto max-h-[300px]">
              <pre className="text-[11px] font-mono text-indigo-300 leading-relaxed">
                {JSON.stringify(record.raw_data, null, 2)}
              </pre>
            </div>
            <p className="text-[10px] text-slate-500">
              Note: This represents the immutable raw record captured directly from the flat file upload for audit completeness.
            </p>
          </div>
        </div>

      </div>

      <RejectModal
        isOpen={isRejectOpen}
        onClose={() => setIsRejectOpen(false)}
        onConfirm={handleRejectConfirm}
        recordId={id}
      />
    </div>
  );
}
