import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import client from '../api/client';
import StatusCard from '../components/StatusCard';
import FlagBadge from '../components/FlagBadge';
import RejectModal from '../components/RejectModal';
import { 
  BarChart3, ShieldAlert, CheckCircle, XOctagon, Inbox, 
  Leaf, RotateCcw, ArrowUpRight, Search, Eye, Filter, ChevronUp, ChevronDown
} from 'lucide-react';

export default function Dashboard() {
  // Stats
  const [stats, setStats] = useState({
    total_records: 0, pending: 0, flagged: 0, approved: 0, rejected: 0, approved_co2e: 0
  });
  
  // Records
  const [records, setRecords] = useState([]);
  const [loading, setLoading] = useState(true);
  
  // Filters
  const [sourceType, setSourceType] = useState('');
  const [scope, setScope] = useState('');
  const [status, setStatus] = useState('');
  const [search, setSearch] = useState('');
  
  // Selection
  const [selectedIds, setSelectedIds] = useState([]);
  
  // Modal State
  const [rejectingId, setRejectingId] = useState(null);
  const [isRejectOpen, setIsRejectOpen] = useState(false);

  // Section Collapse states
  const [isFiltersExpanded, setIsFiltersExpanded] = useState(true);
  const [isKpisExpanded, setIsKpisExpanded] = useState(true);

  // Safe-guards for rendering stats KPIs
  const totalRecords = stats?.total_records ?? 0;
  const pendingRecords = stats?.pending ?? 0;
  const flaggedRecords = stats?.flagged ?? 0;
  const approvedRecords = stats?.approved ?? 0;
  const rejectedRecords = stats?.rejected ?? 0;
  const approvedCo2e = stats?.approved_co2e ?? 0;

  const fetchStats = async () => {
    try {
      const res = await client.get('/dashboard/stats/');
      setStats(res.data);
    } catch (err) {
      console.error('Error fetching stats:', err);
    }
  };

  const fetchRecords = async () => {
    setLoading(true);
    try {
      const params = {};
      if (sourceType) params.source_type = sourceType;
      if (scope) params.scope = scope;
      if (status) params.status = status;
      
      const res = await client.get('/records/', { params });
      setRecords(res.data);
    } catch (err) {
      console.error('Error fetching records:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStats();
  }, []);

  useEffect(() => {
    fetchRecords();
    setSelectedIds([]); // Reset selection when filters change
  }, [sourceType, scope, status]);

  const handleApprove = async (id) => {
    try {
      await client.post(`/records/${id}/approve/`);
      fetchRecords();
      fetchStats();
    } catch (err) {
      alert('Failed to approve record: ' + (err.response?.data?.error || err.message));
    }
  };

  const handleRejectTrigger = (id) => {
    console.log('Reject button clicked inside Dashboard table row! Record ID:', id);
    setRejectingId(id);
    setIsRejectOpen(true);
  };

  const handleRejectConfirm = async (id, note) => {
    await client.post(`/records/${id}/reject/`, { note });
    fetchRecords();
    fetchStats();
  };

  const handleBulkApprove = async () => {
    if (selectedIds.length === 0) return;
    if (window.confirm(`Are you sure you want to bulk-approve the ${selectedIds.length} selected records?`)) {
      try {
        const res = await client.post('/records/bulk-approve/', { ids: selectedIds });
        alert(res.data.message);
        fetchRecords();
        fetchStats();
        setSelectedIds([]);
      } catch (err) {
        alert('Bulk approval failed.');
      }
    }
  };

  const handleSelectAll = (e) => {
    if (e.target.checked) {
      // Select all non-approved IDs
      const nonApproved = records
        .filter(r => r.status !== 'APPROVED')
        .map(r => r.id);
      setSelectedIds(nonApproved);
    } else {
      setSelectedIds([]);
    }
  };

  const handleSelectRow = (id) => {
    if (selectedIds.includes(id)) {
      setSelectedIds(selectedIds.filter(x => x !== id));
    } else {
      setSelectedIds([...selectedIds, id]);
    }
  };

  const resetFilters = () => {
    setSourceType('');
    setScope('');
    setStatus('');
    setSearch('');
  };

  // Local text filter
  const filteredRecords = (records || []).filter(r => {
    if (!search) return true;
    const term = search.toLowerCase();
    return (
      (r.activity_type && r.activity_type.toLowerCase().includes(term)) ||
      (r.raw_data?.meter_id && String(r.raw_data.meter_id).toLowerCase().includes(term)) ||
      (r.raw_data?.Belegnum && String(r.raw_data.Belegnum).toLowerCase().includes(term)) ||
      (r.raw_data?.transaction_id && String(r.raw_data.transaction_id).toLowerCase().includes(term))
    );
  });

  const nonApprovedRecords = (records || []).filter(r => r.status !== 'APPROVED');
  const isAllSelected = records?.length > 0 && nonApprovedRecords.length > 0 && selectedIds.length === nonApprovedRecords.length;

  return (
    <div className="space-y-8">
      {/* Top Section */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <h2 className="text-3xl font-extrabold tracking-tight text-slate-100">Review Dashboard</h2>
          <p className="text-sm text-slate-400 mt-1">
            Analyze, audit, and approve corporate emissions records prior to final financial ESG compliance reporting.
          </p>
        </div>
        
        <div className="flex items-center gap-3">
          <button 
            onClick={() => setIsKpisExpanded(!isKpisExpanded)}
            className="flex items-center gap-2 px-4 py-2 bg-slate-900 border border-slate-800 text-slate-300 rounded-xl hover:text-slate-100 hover:border-slate-700 transition-all text-sm font-semibold cursor-pointer shadow-sm hover:shadow"
            title={isKpisExpanded ? "Hide Analytics summary to save space" : "Show Analytics summary"}
          >
            {isKpisExpanded ? (
              <>
                Hide Summary <ChevronUp className="w-4 h-4" />
              </>
            ) : (
              <>
                Show Summary <ChevronDown className="w-4 h-4" />
              </>
            )}
          </button>

          <button 
            onClick={() => { fetchStats(); fetchRecords(); }}
            className="flex items-center gap-2 px-4 py-2 bg-slate-900 border border-slate-800 text-slate-300 rounded-xl hover:text-slate-100 hover:border-slate-700 transition-all text-sm font-semibold"
          >
            <RotateCcw className="w-4 h-4" /> Reload Data
          </button>
        </div>
      </div>

      {/* KPI Cards */}
      <div className={`grid transition-all duration-300 ease-in-out ${
        isKpisExpanded 
          ? 'grid-rows-[1fr] opacity-100' 
          : 'grid-rows-[0fr] opacity-0 overflow-hidden'
      }`}>
        <div className="overflow-hidden">
          <div className="grid grid-cols-2 lg:grid-cols-6 gap-4 pb-1">
            <StatusCard 
              title="Total Records" 
              value={totalRecords} 
              icon={Inbox} 
              color="slate" 
            />
            <StatusCard 
              title="Pending" 
              value={pendingRecords} 
              icon={Inbox} 
              color="indigo" 
            />
            <StatusCard 
              title="Flagged" 
              value={flaggedRecords} 
              icon={ShieldAlert} 
              color="amber" 
            />
            <StatusCard 
              title="Approved" 
              value={approvedRecords} 
              icon={CheckCircle} 
              color="emerald" 
            />
            <StatusCard 
              title="Rejected" 
              value={rejectedRecords} 
              icon={XOctagon} 
              color="red" 
            />
            <StatusCard 
              title="Approved CO2e" 
              value={`${(approvedCo2e / 1000).toFixed(2)} t`} 
              icon={Leaf} 
              color="rose"
              subtitle={`${approvedCo2e.toLocaleString()} kg`}
            />
          </div>
        </div>
      </div>

      {/* Filters & Search */}
      <div className="glass bg-[#0d1424]/40 p-10 rounded-3xl border-2 border-emerald-500/25 space-y-6 shadow-2xl relative overflow-hidden border-t-8 border-t-emerald-500">
        <div className="flex items-center justify-between pb-4 border-b border-slate-900">
          <span className="text-xl md:text-2xl font-extrabold text-slate-100 uppercase tracking-widest flex items-center gap-3">
            <Filter className="w-7 h-7 text-emerald-500" />
            Query Filters
          </span>
          <div className="flex items-center gap-3">
            <button 
              onClick={() => setIsFiltersExpanded(!isFiltersExpanded)}
              className="flex items-center gap-2 px-5 py-2.5 bg-slate-100 hover:bg-slate-200 text-slate-200 rounded-full transition-all text-sm font-extrabold shadow-sm hover:shadow cursor-pointer"
              title={isFiltersExpanded ? "Hide filter controls to save space" : "Show filter controls"}
            >
              {isFiltersExpanded ? (
                <>
                  Hide Filters <ChevronUp className="w-4 h-4" />
                </>
              ) : (
                <>
                  Show Filters <ChevronDown className="w-4 h-4" />
                </>
              )}
            </button>
            <button 
              onClick={resetFilters}
              className="flex items-center gap-2 px-5 py-2.5 bg-slate-100 hover:bg-slate-200 text-slate-200 rounded-full transition-all text-sm font-extrabold shadow-sm hover:shadow"
            >
              <RotateCcw className="w-4 h-4" /> Clear All Filters
            </button>
          </div>
        </div>
        
        <div className={`grid transition-all duration-300 ease-in-out ${
          isFiltersExpanded 
            ? 'grid-rows-[1fr] opacity-100' 
            : 'grid-rows-[0fr] opacity-0 overflow-hidden'
        }`}>
          <div className="overflow-hidden">
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-8 pt-2">
              {/* Source Type Filter */}
              <div className="relative group">
                <label className="block text-sm font-black text-slate-500 mb-2.5 uppercase tracking-widest transition-all">
                  Source Category
                </label>
                <select
                  value={sourceType}
                  onChange={(e) => setSourceType(e.target.value)}
                  className="large-filter-input w-full"
                >
                  <option value="">All Categories</option>
                  <option value="SAP">SAP (Scope 1)</option>
                  <option value="UTILITY">Utility (Scope 2)</option>
                  <option value="TRAVEL">Travel (Scope 3)</option>
                </select>
              </div>

              {/* Scope Filter */}
              <div className="relative group">
                <label className="block text-sm font-black text-slate-500 mb-2.5 uppercase tracking-widest transition-all">
                  Carbon Scope
                </label>
                <select
                  value={scope}
                  onChange={(e) => setScope(e.target.value)}
                  className="large-filter-input w-full"
                >
                  <option value="">All Scopes</option>
                  <option value="1">Scope 1 - Direct</option>
                  <option value="2">Scope 2 - Indirect</option>
                  <option value="3">Scope 3 - Value Chain</option>
                </select>
              </div>

              {/* Status Filter */}
              <div className="relative group">
                <label className="block text-sm font-black text-slate-500 mb-2.5 uppercase tracking-widest transition-all">
                  Validation Status
                </label>
                <select
                  value={status}
                  onChange={(e) => setStatus(e.target.value)}
                  className="large-filter-input w-full"
                >
                  <option value="">All Statuses</option>
                  <option value="PENDING">Pending Review</option>
                  <option value="FLAGGED">Flagged Anomalies</option>
                  <option value="APPROVED">Approved Records</option>
                  <option value="REJECTED">Rejected Records</option>
                </select>
              </div>

              {/* Search bar */}
              <div className="relative group">
                <label className="block text-sm font-black text-slate-500 mb-2.5 uppercase tracking-widest transition-all">
                  Search Keywords
                </label>
                <div className="relative animate-pulse-subtle">
                  <input
                    type="text"
                    placeholder="e.g. meter, document..."
                    value={search}
                    onChange={(e) => setSearch(e.target.value)}
                    className="large-filter-input large-filter-input-search w-full"
                  />
                  <Search className="absolute left-5 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400 pointer-events-none group-hover:text-emerald-500 transition-colors" />
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Bulk actions bar */}
      {selectedIds.length > 0 && (
        <div className="glass bg-brand-500/10 border border-brand-500/20 p-4 rounded-xl flex items-center justify-between animate-fadeIn">
          <span className="text-xs font-bold text-brand-300">
            {selectedIds.length} records selected for review
          </span>
          <button
            onClick={handleBulkApprove}
            className="px-4 py-1.5 text-xs font-bold text-slate-950 bg-brand-400 hover:bg-brand-500 rounded-lg shadow-lg shadow-brand-500/25 transition-all"
          >
            Bulk Approve Selected
          </button>
        </div>
      )}

      {/* Main Data Table */}
      <div className="glass bg-slate-900/10 rounded-2xl border border-slate-850 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="border-b border-slate-850 bg-slate-900/30 text-slate-400 text-xs font-bold uppercase tracking-wider">
                <th className="py-4 px-4 w-10 text-center">
                  <input
                    type="checkbox"
                    onChange={handleSelectAll}
                    checked={isAllSelected}
                    className="rounded border-slate-800 bg-slate-950 text-brand-500 focus:ring-brand-500"
                  />
                </th>
                <th className="py-4 px-4">Source</th>
                <th className="py-4 px-4">Activity Type</th>
                <th className="py-4 px-4">Reporting Period</th>
                <th className="py-4 px-4 text-right">Raw Value</th>
                <th className="py-4 px-4 text-right">Normalized</th>
                <th className="py-4 px-4 text-right">CO2e (kg)</th>
                <th className="py-4 px-4 text-center">Status</th>
                <th className="py-4 px-4">Anomalous Flags</th>
                <th className="py-4 px-4 text-center">Actions</th>
              </tr>
            </thead>
            
            <tbody className="divide-y divide-slate-850 text-slate-200 text-xs font-medium">
              {loading ? (
                <tr>
                  <td colSpan="10" className="py-12 text-center text-slate-500">
                    <span className="inline-block animate-spin border-2 border-brand-500 border-t-transparent w-6 h-6 rounded-full mr-2 align-middle"></span>
                    Loading emission records...
                  </td>
                </tr>
              ) : filteredRecords.length === 0 ? (
                <tr>
                  <td colSpan="10" className="py-12 text-center text-slate-500">
                    No matching carbon records found.
                  </td>
                </tr>
              ) : (
                filteredRecords.map((r) => {
                  const isApproved = r.status === 'APPROVED';
                  const isRejected = r.status === 'REJECTED';
                  const isFlagged = r.status === 'FLAGGED';
                  
                  return (
                    <tr 
                      key={r.id} 
                      className={`hover:bg-slate-900/35 transition-colors duration-150 ${isApproved ? 'bg-emerald-950/5' : ''}`}
                    >
                      {/* Checkbox */}
                      <td className="py-3 px-4 text-center">
                        <input
                          type="checkbox"
                          disabled={isApproved}
                          checked={selectedIds.includes(r.id)}
                          onChange={() => handleSelectRow(r.id)}
                          className={`rounded border-slate-800 bg-slate-950 text-brand-500 focus:ring-brand-500 ${isApproved ? 'opacity-30 cursor-not-allowed' : ''}`}
                        />
                      </td>

                      {/* Source */}
                      <td className="py-3 px-4">
                        <span className={`px-2 py-0.5 rounded font-bold uppercase tracking-wider text-[10px] ${
                          r.source_type === 'SAP' 
                            ? 'bg-blue-500/10 text-blue-400' 
                            : r.source_type === 'UTILITY' 
                            ? 'bg-indigo-500/10 text-indigo-400' 
                            : 'bg-rose-500/10 text-rose-400'
                        }`}>
                          {r.source_type}
                        </span>
                        <span className="text-[10px] text-slate-500 block mt-1">Scope {r.scope}</span>
                      </td>

                      {/* Activity */}
                      <td className="py-3 px-4">
                        <span className="font-bold text-slate-300 capitalize">{r.activity_type.replace('_', ' ')}</span>
                      </td>

                      {/* Period */}
                      <td className="py-3 px-4 text-slate-400">
                        {r.period_start === r.period_end ? (
                          <span>{r.period_start}</span>
                        ) : (
                          <span>{r.period_start} <span className="text-slate-600">to</span> {r.period_end}</span>
                        )}
                      </td>

                      {/* Raw */}
                      <td className="py-3 px-4 text-right text-slate-400 font-mono">
                        {(r.raw_value || 0).toLocaleString(undefined, {minimumFractionDigits: 1, maximumFractionDigits: 2})} {r.raw_unit}
                      </td>

                      {/* Normalized */}
                      <td className="py-3 px-4 text-right text-slate-300 font-mono">
                        {(r.normalized_value || 0).toLocaleString(undefined, {minimumFractionDigits: 1, maximumFractionDigits: 2})} {r.normalized_unit}
                      </td>

                      {/* CO2e */}
                      <td className="py-3 px-4 text-right text-brand-300 font-bold font-mono">
                        {(r.co2e_kg || 0).toLocaleString(undefined, {minimumFractionDigits: 1, maximumFractionDigits: 1})}
                      </td>

                      {/* Status */}
                      <td className="py-3 px-4 text-center">
                        <span className={`px-2 py-0.5 rounded-full font-bold uppercase text-[9px] border ${
                          isApproved
                            ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20'
                            : isRejected
                            ? 'bg-rose-500/10 text-rose-400 border-rose-500/20'
                            : isFlagged
                            ? 'bg-amber-500/10 text-amber-400 border-amber-500/20'
                            : 'bg-indigo-500/10 text-indigo-400 border-indigo-500/20'
                        }`}>
                          {r.status}
                        </span>
                      </td>

                      {/* Flags */}
                      <td className="py-3 px-4">
                        <div className="flex flex-wrap gap-1 max-w-[200px]">
                          {r.flags && r.flags.length > 0 ? (
                            r.flags.map((f) => (
                              <FlagBadge key={f.id} type={f.flag_type} message={f.message} />
                            ))
                          ) : (
                            <span className="text-slate-600 text-[10px] italic">No flags</span>
                          )}
                        </div>
                      </td>

                      {/* Actions */}
                      <td className="py-3 px-4 text-center">
                        <div className="flex items-center justify-center gap-2">
                          <Link
                            to={`/records/${r.id}`}
                            className="p-1.5 bg-slate-950 hover:bg-slate-850 text-slate-400 hover:text-slate-200 border border-slate-800 rounded-lg transition-colors"
                            title="View Full Detail Audit Trail"
                          >
                            <Eye className="w-3.5 h-3.5" />
                          </Link>
                          
                          {isApproved ? (
                            <span className="text-[10px] text-emerald-500 font-bold uppercase select-none flex items-center gap-0.5">
                              <CheckCircle className="w-3 h-3" /> Locked
                            </span>
                          ) : (
                            <>
                              <button
                                onClick={() => handleApprove(r.id)}
                                className="px-2 py-1 bg-emerald-500 hover:bg-emerald-600 text-slate-950 font-extrabold rounded text-[10px] transition-colors"
                                title="Approve emission number"
                              >
                                Approve
                              </button>
                              <button
                                onClick={() => handleRejectTrigger(r.id)}
                                className="px-2 py-1 bg-rose-500/10 hover:bg-rose-500 text-rose-400 hover:text-slate-950 border border-rose-500/20 rounded text-[10px] transition-all"
                                title="Reject and request corrections"
                              >
                                Reject
                              </button>
                            </>
                          )}
                        </div>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Reject Modal */}
      <RejectModal
        isOpen={isRejectOpen}
        onClose={() => setIsRejectOpen(false)}
        onConfirm={handleRejectConfirm}
        recordId={rejectingId}
      />
    </div>
  );
}
