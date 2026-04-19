import React from 'react';
import { BrowserRouter, Routes, Route, Link, useLocation } from 'react-router-dom';
import { Activity, PlayCircle, List, Sun, Moon } from 'lucide-react';
import Dashboard from './pages/Dashboard';
import ReplayMode from './pages/ReplayMode';
import EventLog from './pages/EventLog';
import { useWebSocket } from './hooks/useWebSocket';
import { ThemeProvider, useTheme } from './context/ThemeContext';

const NavLink = ({ to, icon, label }) => {
  const location = useLocation();
  const isActive = location.pathname === to;
  const { isDarkMode } = useTheme();
  
  return (
    <Link 
      to={to} 
      className={`flex items-center space-x-3 px-4 py-3 rounded-lg transition-all duration-200 ${
        isActive 
          ? (isDarkMode ? 'bg-slate-800 text-white shadow-lg shadow-black/20' : 'bg-white text-blue-600 shadow-md ring-1 ring-slate-200')
          : (isDarkMode ? 'text-slate-500 hover:bg-slate-800 hover:text-white' : 'text-slate-500 hover:bg-white hover:text-blue-600')
      }`}
    >
      {icon}
      <span className="font-medium">{label}</span>
    </Link>
  );
};

const Layout = ({ children }) => {
  const { isConnected } = useWebSocket();
  const { isDarkMode, toggleTheme } = useTheme();
  
  return (
    <div className={`flex h-screen overscroll-none overflow-hidden transition-colors duration-300 ${isDarkMode ? 'bg-slate-900 text-white' : 'bg-slate-50 text-slate-900'}`}>
      {/* Sidebar */}
      <aside className={`w-64 border-r flex flex-col transition-colors duration-300 ${isDarkMode ? 'bg-slate-950 border-slate-800' : 'bg-slate-50 border-slate-200'}`}>
        <div className="p-6">
          <h1 className={`text-xl font-bold bg-gradient-to-r from-blue-400 to-indigo-400 bg-clip-text text-transparent`}>
            Stampede Predictor
          </h1>
          <p className="text-xs mt-1 text-slate-500 uppercase tracking-widest font-bold opacity-70">Lakshya 2.0 • TS-11</p>
        </div>
        
        <nav className="flex-1 px-4 space-y-2 mt-4">
          <NavLink to="/" icon={<Activity size={20} />} label="Live Dashboard" />
          <NavLink to="/replay" icon={<PlayCircle size={20} />} label="Replay Mode" />
          <NavLink to="/events" icon={<List size={20} />} label="Event Archive" />
        </nav>

        {/* Theme Toggle */}
        <div className="px-4 mb-4">
          <button
            onClick={toggleTheme}
            className={`w-full flex items-center justify-between px-4 py-3 rounded-xl transition-all duration-300 ${
              isDarkMode 
                ? 'bg-slate-900 text-slate-400 hover:text-white border border-slate-800' 
                : 'bg-white text-slate-600 hover:text-blue-600 border border-slate-200 shadow-sm'
            }`}
          >
            <span className="text-xs font-black uppercase tracking-widest">
              {isDarkMode ? 'Dark Mode' : 'Light Mode'}
            </span>
            {isDarkMode ? <Moon size={16} /> : <Sun size={16} />}
          </button>
        </div>
        
        <div className={`p-4 border-t ${isDarkMode ? 'border-slate-800' : 'border-slate-200'}`}>
          <div className={`flex items-center space-x-2 px-4 py-2 rounded-lg ${isDarkMode ? 'bg-slate-900' : 'bg-white border border-slate-100 shadow-sm'}`}>
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
            <span className={`text-sm font-medium ${isDarkMode ? 'text-slate-300' : 'text-slate-600'}`}>
              {isConnected ? 'LIVE FEED ON' : 'CONNECTING...'}
            </span>
          </div>
        </div>
      </aside>
      
      {/* Main Content */}
      <main className={`flex-1 overflow-auto ${isDarkMode ? 'bg-slate-900' : 'bg-slate-50'}`}>
        {children}
      </main>
    </div>
  );
};

function AppContent() {
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

function App() {
  return (
    <ThemeProvider>
       <AppContent />
    </ThemeProvider>
  );
}

export default App;
