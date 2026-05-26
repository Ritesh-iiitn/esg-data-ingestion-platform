import React, { useState, useEffect } from 'react';
import client from '../api/client';
import UploadBox from '../components/UploadBox';
import { Layers, Database, Calendar, CheckCircle2, XCircle, Loader2 } from 'lucide-react';

export default function Upload() {
  const [uploads, setUploads] = useState([]);
  const [loading, setLoading] = useState(true);

  const fetchUploadHistory = async () => {
    try {
      const res = await client.get('/uploads/');
      setUploads(res.data);
    } catch (err) {
      console.error('Error fetching upload history:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchUploadHistory();
    // Poll for status updates while any upload is PROCESSING
    const interval = setInterval(() => {
      if (uploads.some(u => u.status === 'PROCESSING')) {
        fetchUploadHistory();
      }
    }, 4000);
    return () => clearInterval(interval);
  }, [uploads]);

  const handleUploadApi = async (sourceType, formData) => {
    const res = await client.post(`/upload/${sourceType.toLowerCase()}/`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    fetchUploadHistory();
    return res.data;
  };

  const getStatusBadge = (status) => {
    switch (status) {
      case 'DONE':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
            <CheckCircle2 className="w-3.5 h-3.5" /> Done
          </span>
        );
      case 'FAILED':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-rose-500/10 text-rose-400 border border-rose-500/20">
            <XCircle className="w-3.5 h-3.5" /> Failed
          </span>
        );
      case 'PROCESSING':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-blue-500/10 text-blue-400 border border-blue-500/20">
            <Loader2 className="w-3.5 h-3.5 animate-spin" /> Processing
          </span>
        );
      default:
        return <span className="text-xs text-slate-400">{status}</span>;
    }
  };

  const filterUploads = (source) => uploads.filter(u => u.source_type === source);

  return (
    <div className="space-y-10">
      <div>
        <h2 className="text-3xl font-extrabold tracking-tight text-slate-100">Data Ingestion Center</h2>
        <p className="text-sm text-slate-400 mt-1">
          Upload emissions reports from your ERP, utility portals, and travel managers to normalize and review.
        </p>
      </div>

      {/* Grid of upload zones */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <UploadBox 
          title="SAP - Scope 1" 
          subtitle="Fuel logs and procurement CSV files. Handles Plant code, bookings, and material groups."
          sourceType="SAP"
          onUpload={(fd) => handleUploadApi('SAP', fd)}
        />
        
        <UploadBox 
          title="Utility - Scope 2" 
          subtitle="Electricity meter portal CSV dumps. Handles consumption billing periods and tariff codes."
          sourceType="UTILITY"
          onUpload={(fd) => handleUploadApi('UTILITY', fd)}
        />
        
        <UploadBox 
          title="Corporate Travel - Scope 3" 
          subtitle="Concur-style flight, hotel, and rental car CSV records. Computes distances and lodging nights."
          sourceType="TRAVEL"
          onUpload={(fd) => handleUploadApi('TRAVEL', fd)}
        />
      </div>

      {/* Upload history grids */}
      <div className="space-y-8 mt-12">
        <h3 className="text-xl font-bold text-slate-200 border-b border-slate-800 pb-3 flex items-center gap-2">
          <Database className="w-5 h-5 text-brand-400" />
          Ingestion History & Status
        </h3>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {['SAP', 'UTILITY', 'TRAVEL'].map((source) => {
            const list = filterUploads(source);
            return (
              <div key={source} className="glass p-5 rounded-2xl bg-slate-900/30 flex flex-col h-[350px]">
                <h4 className="font-bold text-slate-300 border-b border-slate-800 pb-2 mb-4 text-sm tracking-wider uppercase flex items-center gap-1.5">
                  <span className="w-2 h-2 rounded-full bg-brand-500"></span>
                  {source} Ingest Logs
                </h4>
                
                <div className="overflow-y-auto flex-grow pr-1 space-y-3">
                  {loading ? (
                    <div className="flex justify-center items-center h-full">
                      <Loader2 className="w-6 h-6 animate-spin text-brand-400" />
                    </div>
                  ) : list.length === 0 ? (
                    <div className="flex flex-col items-center justify-center h-full text-slate-600 text-xs">
                      <Calendar className="w-8 h-8 mb-2" />
                      No history found
                    </div>
                  ) : (
                    list.map((u) => (
                      <div key={u.id} className="p-3 bg-slate-950/50 border border-slate-850 rounded-xl space-y-2 hover:border-slate-700 transition-all duration-150">
                        <div className="flex justify-between items-center">
                          <span className="text-xs font-semibold text-slate-300 truncate max-w-[120px]" title={u.uploaded_file}>
                            {u.uploaded_file.split('/').pop()}
                          </span>
                          {getStatusBadge(u.status)}
                        </div>
                        
                        <div className="flex justify-between items-center text-[10px] text-slate-500">
                          <span>{new Date(u.uploaded_at).toLocaleString()}</span>
                          <span className="font-bold text-slate-400">
                            {u.status === 'DONE' ? `${u.row_count} rows` : '—'}
                          </span>
                        </div>
                      </div>
                    ))
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
