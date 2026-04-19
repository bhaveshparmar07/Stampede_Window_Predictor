import React, { useState } from 'react';
import { Shield, Home, Bus, CheckCircle } from 'lucide-react';
import { AGENCIES, ALERT_SLA_SEC } from '../utils/constants';
import { useTheme } from '../context/ThemeContext';

const AgencyPanel = ({ agencyKey, alert, onAcknowledge }) => {
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isHovered, setIsHovered] = useState(false);
  const { isDarkMode } = useTheme();
  
  const agency = AGENCIES[agencyKey];
  
  // Get action item for this specific agency from the alert
  const actionObj = alert?.agency_actions?.find(a => a.agency === agencyKey) || null;
  const isAcknowledged = actionObj?.acknowledged || false;
  const responseTime = actionObj?.response_time_sec;
  const isSlaMissed = responseTime > ALERT_SLA_SEC;

  const handleAcknowledgeClick = async () => {
    setIsSubmitting(true);
    try {
      await onAcknowledge(agencyKey);
    } finally {
      setIsSubmitting(false);
    }
  };
  
  // Icon routing
  const getIcon = () => {
    switch(agencyKey) {
      case 'police': return <Shield size={24} />;
      case 'temple': return <Home size={24} />;
      case 'transport': return <Bus size={24} />;
      default: return <Shield size={24} />;
    }
  };

  return (
    <div 
      className={`relative overflow-hidden rounded-xl border transition-all duration-300 ${
        alert 
          ? (isAcknowledged 
              ? (isDarkMode ? 'border-green-500/30 bg-slate-900/40' : 'border-green-500/30 bg-green-50/30') 
              : (isDarkMode ? 'border-red-500/50 shadow-[0_0_15px_rgba(239,68,68,0.15)] bg-slate-900' : 'border-red-500/50 shadow-[0_0_15px_rgba(239,68,68,0.1)] bg-white'))
          : (isDarkMode ? 'border-slate-800 bg-slate-900/20' : 'border-slate-200 bg-white shadow-sm hover:shadow-md')
      }`}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
    >
      {/* Header */}
      <div className={`p-4 flex items-center justify-between border-b transition-colors duration-300 ${
        alert 
          ? (isAcknowledged ? 'border-green-500/20 bg-green-500/5' : 'border-red-500/20 bg-red-500/10') 
          : (isDarkMode ? 'border-slate-800 bg-slate-800/50' : 'border-slate-100 bg-slate-50/50')
      }`}>
        <div className="flex items-center space-x-3">
          <div className={
            alert ? (isAcknowledged ? 'text-green-400' : 'text-red-400') : 'text-slate-500'
          }>
            {getIcon()}
          </div>
          <h3 className={`font-bold tracking-wide ${isDarkMode ? 'text-slate-200' : 'text-slate-900'}`}>{agency?.label}</h3>
        </div>
        
        {/* Status Badge */}
        {alert && (
          <div className={`px-2.5 py-1 flex items-center space-x-1.5 text-[10px] font-black rounded uppercase tracking-widest ${
            isAcknowledged ? 'bg-green-500/20 text-green-400' : 'bg-red-500 text-white animate-pulse'
          }`}>
            {isAcknowledged ? (
              <>
                <CheckCircle size={12} />
                <span>Acknowledged</span>
              </>
            ) : (
              <span>Pending Action</span>
            )}
          </div>
        )}
      </div>
      
      {/* Content */}
      <div className="p-5">
        <p className={`text-sm font-medium min-h-12 leading-relaxed opacity-80 ${isDarkMode ? 'text-slate-300' : 'text-slate-600'}`}>
          {actionObj ? actionObj.action : agency?.action}
        </p>
        
        <div className="mt-5 flex items-end justify-between">
          <div className="flex flex-col">
            <span className="text-[10px] font-black text-slate-500 uppercase tracking-widest mb-1.5">Response Time</span>
            <div className="text-2xl font-black tabular-nums tracking-tight">
              {isAcknowledged ? (
                <span className={isSlaMissed ? 'text-yellow-400' : 'text-green-400'}>
                  {String(Math.floor(responseTime / 60)).padStart(2, '0')}:
                  {String(responseTime % 60).padStart(2, '0')}
                </span>
              ) : (
                <span className={isDarkMode ? 'text-slate-700' : 'text-slate-300'}>--:--</span>
              )}
            </div>
          </div>
          
          <button
            onClick={handleAcknowledgeClick}
            disabled={!alert || isAcknowledged || isSubmitting}
            className={`px-5 py-2.5 rounded-lg font-black text-xs uppercase tracking-widest transition-all z-10 ${
              !alert 
                ? (isDarkMode ? 'bg-slate-800 text-slate-600' : 'bg-slate-100 text-slate-400') + ' cursor-not-allowed opacity-50' 
                : isAcknowledged 
                  ? (isDarkMode ? 'bg-green-500/10 text-green-500/50 border-green-500/20' : 'bg-green-50 text-green-500/40 border-green-100') + ' cursor-not-allowed border'
                  : isSubmitting
                    ? 'bg-red-900 text-white animate-pulse cursor-wait'
                    : 'bg-red-600 hover:bg-red-500 text-white shadow-lg shadow-red-500/20 cursor-pointer transform hover:-translate-y-0.5 active:translate-y-0'
            }`}
          >
            {isSubmitting ? 'Processing...' : isAcknowledged ? 'Confirmed' : 'Acknowledge'}
          </button>
        </div>
      </div>
      
      {alert && !isAcknowledged && (
        <div className="absolute inset-0 border-2 border-red-500/50 rounded-xl pointer-events-none animate-pulse-fast"></div>
      )}
    </div>
  );
};

export default AgencyPanel;
