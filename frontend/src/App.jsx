import React from 'react';
import { BrowserRouter, Routes, Route, Link, useLocation } from 'react-router-dom';
import { Activity, PlayCircle, List } from 'lucide-react';
import Dashboard from './pages/Dashboard';
import ReplayMode from './pages/ReplayMode';
import EventLog from './pages/EventLog';
import { useWebSocket } from './hooks/useWebSocket';

const NavLink = ({ to, icon, label }) => {
  const location = useLocation();
  const isActive = location.pathname === to;
  
  return (
    <Link 
      to={to} 
      className={`flex items-center space-x-3 px-4 py-3 rounded-lg transition-colors ${
        isActive 
          ? 'bg-slate-800 text-white' 
          : 'text-slate-500 hover:bg-slate-800 hover:text-white'
      }`}
    >
      {icon}
      <span className="font-medium">{label}</span>
    </Link>
  );
};

const Layout = ({ children }) => {
  const { isConnected } = useWebSocket();
  
  return (
    <div className="flex h-screen bg-slate-900 text-white overscroll-none overflow-hidden">
      {/* Sidebar */}
      <aside className="w-64 bg-slate-950 border-r border-slate-800 flex flex-col">
        <div className="p-6">
          <h1 className="text-xl font-bold bg-gradient-to-r from-blue-400 to-indigo-400 bg-clip-text text-transparent">
            Stampede Predictor
          </h1>
          <p className="text-xs text-slate-500 mt-1">Lakshya 2.0 • TS-11</p>
        </div>
        
        <nav className="flex-1 px-4 space-y-2 mt-4">
          <NavLink to="/" icon={<Activity size={20} />} label="Live Dashboard" />
          <NavLink to="/replay" icon={<PlayCircle size={20} />} label="Replay Mode" />
          <NavLink to="/events" icon={<List size={20} />} label="Event Archive" />
        </nav>
        
        <div className="p-4 border-t border-slate-800">
          <div className="flex items-center space-x-2 px-4 py-2 rounded-lg bg-slate-900">
            <span className="relative flex h-3 w-3">
              {isConnected ? (
                <>
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
                  <span className="relative inline-flex rounded-full h-3 w-3 bg-green-500"></span>
                </>
              ) : (
                <span className="relative inline-flex rounded-full h-3 w-3 bg-red-500"></span>
              )}
            </span>
            <span className="text-sm font-medium text-slate-300">
              {isConnected ? 'LIVE FEED ON' : 'CONNECTING...'}
            </span>
          </div>
        </div>
      </aside>
      
      {/* Main Content */}
      <main className="flex-1 overflow-auto bg-slate-900">
        {children}
      </main>
    </div>
  );
};

function App() {
  return (
    <BrowserRouter>
      <Layout>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/replay" element={<ReplayMode />} />
          <Route path="/events" element={<EventLog />} />
        </Routes>
      </Layout>
    </BrowserRouter>
  );
}

export default App;
