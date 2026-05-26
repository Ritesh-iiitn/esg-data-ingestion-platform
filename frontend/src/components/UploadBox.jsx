import React, { useState, useRef } from 'react';
import { Upload, FileSpreadsheet, AlertCircle, CheckCircle, RefreshCw } from 'lucide-react';

export default function UploadBox({ title, subtitle, onUpload, sourceType }) {
  const [dragActive, setDragActive] = useState(false);
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  const fileInputRef = useRef(null);

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const droppedFile = e.dataTransfer.files[0];
      if (droppedFile.name.endsWith('.csv')) {
        setFile(droppedFile);
        setError(null);
        setSuccess(null);
      } else {
        setError('Only CSV files are supported.');
      }
    }
  };

  const handleChange = (e) => {
    e.preventDefault();
    if (e.target.files && e.target.files[0]) {
      const selectedFile = e.target.files[0];
      if (selectedFile.name.endsWith('.csv')) {
        setFile(selectedFile);
        setError(null);
        setSuccess(null);
      } else {
        setError('Only CSV files are supported.');
      }
    }
  };

  const triggerInput = () => {
    fileInputRef.current.click();
  };

  const handleUploadSubmit = async () => {
    if (!file) return;
    setLoading(true);
    setError(null);
    setSuccess(null);
    
    try {
      const formData = new FormData();
      formData.append('file', file);
      
      const res = await onUpload(formData);
      setSuccess(`Inported successfully! Ingested ${res.row_count} rows.`);
      setFile(null);
    } catch (err) {
      setError(err.response?.data?.error || 'Ingestion parsing failed. Please check file format.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="glass p-6 rounded-2xl flex flex-col justify-between h-full bg-slate-900/40 relative">
      <div>
        <h4 className="text-lg font-bold text-slate-100 mb-1">{title}</h4>
        <p className="text-xs text-slate-400 mb-6">{subtitle}</p>
        
        <div 
          onDragEnter={handleDrag}
          onDragLeave={handleDrag}
          onDragOver={handleDrag}
          onDrop={handleDrop}
          onClick={triggerInput}
          className={`border-2 border-dashed rounded-xl p-8 flex flex-col items-center justify-center cursor-pointer transition-all duration-200 ${
            dragActive 
              ? 'border-brand-500 bg-brand-500/5' 
              : 'border-slate-800 hover:border-slate-700 bg-slate-950/40'
          }`}
        >
          <input 
            type="file" 
            ref={fileInputRef} 
            onChange={handleChange} 
            accept=".csv"
            className="hidden"
          />
          
          {file ? (
            <div className="flex flex-col items-center text-center">
              <FileSpreadsheet className="w-12 h-12 text-brand-400 mb-3" />
              <p className="text-sm font-semibold text-slate-200 truncate max-w-full">{file.name}</p>
              <p className="text-xs text-slate-500 mt-1">{(file.size / 1024).toFixed(1)} KB</p>
            </div>
          ) : (
            <div className="flex flex-col items-center text-center">
              <Upload className="w-10 h-10 text-slate-500 mb-3" />
              <p className="text-sm text-slate-300 font-medium">Drag & drop CSV or <span className="text-brand-400 font-bold hover:underline">browse</span></p>
              <p className="text-xs text-slate-500 mt-1">Supports standard CSV exports</p>
            </div>
          )}
        </div>
      </div>
      
      <div className="mt-5">
        {error && (
          <div className="mb-4 p-3 bg-red-500/10 border border-red-500/20 text-red-400 rounded-lg text-xs flex items-start gap-2">
            <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
            <span>{error}</span>
          </div>
        )}
        
        {success && (
          <div className="mb-4 p-3 bg-brand-500/10 border border-brand-500/20 text-brand-400 rounded-lg text-xs flex items-start gap-2">
            <CheckCircle className="w-4 h-4 shrink-0 mt-0.5" />
            <span>{success}</span>
          </div>
        )}
        
        <button
          onClick={handleUploadSubmit}
          disabled={!file || loading}
          className={`w-full py-2.5 px-4 rounded-xl text-sm font-bold flex items-center justify-center gap-2 transition-all duration-200 ${
            file && !loading
              ? 'bg-brand-500 hover:bg-brand-600 text-slate-950 font-bold shadow-lg shadow-brand-500/20'
              : 'bg-slate-800 text-slate-500 cursor-not-allowed'
          }`}
        >
          {loading ? (
            <>
              <RefreshCw className="w-4 h-4 animate-spin" />
              Processing File...
            </>
          ) : (
            'Ingest Data'
          )}
        </button>
      </div>
    </div>
  );
}
