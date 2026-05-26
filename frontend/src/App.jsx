import React, { useState } from 'react';
import { BrowserRouter as Router, Routes, Route, Link, Navigate, useLocation } from 'react-router-dom';
import Dashboard from './pages/Dashboard';
import Upload from './pages/Upload';
import RecordDetail from './pages/RecordDetail';
import { LayoutDashboard, CloudUpload, Leaf, AlertCircle, FileText, ChevronLeft, ChevronRight } from 'lucide-react';

function NavigationLayout({ children }) {
  const location = useLocation();
  const path = location.pathname;
  const [isCollapsed, setIsCollapsed] = useState(false);

  const navItems = [
    {
      name: 'Review Dashboard',
      path: '/dashboard',
      icon: LayoutDashboard
    },
    {
      name: 'Ingest Data',
      path: '/upload',
      icon: CloudUpload
    }
  ];

  return (
    <div className="flex h-screen bg-[#070c19] text-slate-100 overflow-hidden font-sans">
      {/* Sidebar Navigation */}
      <aside className={`bg-[#0c1424]/60 border-r border-slate-900 flex flex-col justify-between z-10 glass transition-all duration-300 ease-in-out relative shrink-0 ${
        isCollapsed ? 'w-20 px-3 py-6' : 'w-64 p-6'
      }`}>
        {/* Floating Sidebar Toggle Button - Perfectly centered vertically on the boundary */}
        <button
          onClick={() => setIsCollapsed(!isCollapsed)}
          className="absolute top-[50%] -translate-y-1/2 -right-3.5 w-7 h-7 rounded-full bg-emerald-500 hover:bg-emerald-400 text-slate-950 flex items-center justify-center border-2 border-slate-950 shadow-2xl hover:scale-110 transition-all z-20 cursor-pointer"
          title={isCollapsed ? "Expand Sidebar" : "Collapse Sidebar"}
        >
          {isCollapsed ? <ChevronRight className="w-4 h-4" /> : <ChevronLeft className="w-4 h-4" />}
        </button>

        <div className="space-y-8">
          {/* Logo brand */}
          <div className={`flex items-center gap-3 mt-2 transition-all duration-300 ${isCollapsed ? 'justify-center' : ''}`}>
            <div className="p-2.5 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 shrink-0 shadow-lg">
              <Leaf className="w-6 h-6 animate-pulse" />
            </div>
            {!isCollapsed && (
              <div className="animate-fadeIn">
                <h1 className="text-lg font-black tracking-tight text-white whitespace-nowrap">Breathe ESG</h1>
                <span className="text-[10px] text-emerald-400 font-bold uppercase tracking-wider whitespace-nowrap">Carbon Analytics</span>
              </div>
            )}
          </div>

          {/* Navigation links */}
          <nav className="space-y-2.5">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = path === item.path || (item.path === '/dashboard' && path.startsWith('/records/'));
              
              return (
                <Link
                  key={item.path}
                  to={item.path}
                  className={`flex items-center rounded-xl text-sm font-semibold transition-all duration-200 relative group ${
                    isCollapsed ? 'justify-center p-3 w-12 h-12 mx-auto' : 'px-4 py-3 gap-3 w-full'
                  } ${
                    isActive
                      ? 'bg-emerald-500 text-slate-950 font-bold shadow-lg shadow-emerald-500/25'
                      : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/40'
                  }`}
                  title={isCollapsed ? item.name : undefined}
                >
                  <Icon className="w-5 h-5 shrink-0" />
                  {!isCollapsed && (
                    <span className="animate-fadeIn whitespace-nowrap">
                      {item.name}
                    </span>
                  )}
                  
                  {/* Tooltip on hover when collapsed */}
                  {isCollapsed && (
                    <div className="absolute left-16 bg-slate-950 text-slate-100 text-xs font-bold px-3 py-1.5 rounded-lg opacity-0 scale-95 translate-x-[-10px] group-hover:opacity-100 group-hover:scale-100 group-hover:translate-x-0 transition-all duration-200 pointer-events-none whitespace-nowrap shadow-2xl border border-slate-800 z-30">
                      {item.name}
                    </div>
                  )}
                </Link>
              );
            })}
          </nav>
        </div>

        {/* Analyst User profile status badge */}
        <div className={`bg-[#050912]/80 border border-slate-900 rounded-xl transition-all duration-300 ${
          isCollapsed ? 'p-1.5 mx-auto' : 'p-4 space-y-2'
        }`}>
          <div className={`flex items-center transition-all duration-300 ${isCollapsed ? 'justify-center p-0.5' : 'gap-3'}`}>
            <div className="w-8 h-8 rounded-full bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center font-black text-emerald-400 text-xs shrink-0 shadow-inner">
              AN
            </div>
            {!isCollapsed && (
              <div className="animate-fadeIn">
                <h4 className="text-xs font-bold text-slate-200 whitespace-nowrap">ESG Lead Analyst</h4>
                <span className="text-[10px] text-emerald-400 font-medium flex items-center gap-1 whitespace-nowrap">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 inline-block animate-pulse"></span>
                  Active Compliance
                </span>
              </div>
            )}
          </div>
        </div>
      </aside>

      {/* Main Workspace Area */}
      <main className="flex-grow overflow-y-auto p-8 relative transition-all duration-300">
        {/* Background ambient lighting effects */}
        <div className="absolute top-0 right-1/4 w-[500px] h-[500px] rounded-full bg-emerald-500/5 filter blur-[120px] pointer-events-none"></div>
        <div className="absolute bottom-0 left-1/3 w-[400px] h-[400px] rounded-full bg-indigo-500/5 filter blur-[120px] pointer-events-none"></div>
        
        <div className="max-w-7xl mx-auto relative z-10">
          {children}
        </div>
      </main>
    </div>
  );
}

export default function App() {
  return (
    <Router>
      <NavigationLayout>
        <Routes>
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/upload" element={<Upload />} />
          <Route path="/records/:id" element={<RecordDetail />} />
          <Route path="*" element={<Navigate to="/dashboard" replace />} />
        </Routes>
      </NavigationLayout>
    </Router>
  );
}
