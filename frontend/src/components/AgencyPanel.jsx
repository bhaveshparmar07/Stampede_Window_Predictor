import React, { useState } from 'react';
import { Shield, Home, Bus, CheckCircle } from 'lucide-react';
import { AGENCIES, ALERT_SLA_SEC } from '../utils/constants';

const AgencyPanel = ({ agencyKey, alert, onAcknowledge }) => {
  const [isHovered, setIsHovered] = useState(false);
  const agency = AGENCIES[agencyKey];
  
  // Get action item for this specific agency from the alert
  const actionObj = alert?.agency_actions?.find(a => a.agency === agencyKey) || null;
  const isAcknowledged = actionObj?.acknowledged || false;
  const responseTime = actionObj?.response_time_sec;
  
  const isSlaMissed = responseTime > ALERT_SLA_SEC;
  
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
      className={`relative overflow-hidden rounded-xl border bg-slate-900 transition-all duration-300 ${
        alert ? (isAcknowledged ? 'border-green-500/30' : 'border-red-500/50 shadow-[0_0_15px_rgba(239,68,68,0.15)]') : 'border-slate-800'
      }`}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
    >
      {/* Header */}
      <div className={`p-4 flex items-center justify-between border-b ${
        alert ? (isAcknowledged ? 'border-green-500/20 bg-green-500/5' : 'border-red-500/20 bg-red-500/10') : 'border-slate-800 bg-slate-800/50'
      }`}>
        <div className="flex items-center space-x-3">
          <div className={
            alert ? (isAcknowledged ? 'text-green-400' : 'text-red-400') : 'text-slate-500'
          }>
            {getIcon()}
          </div>
          <h3 className="font-bold text-slate-200 tracking-wide">{agency.label}</h3>
        </div>
        
        {/* Status Badge */}
        {alert && (
          <div className={`px-2 py-1 flex items-center space-x-1 text-xs font-bold rounded-sm uppercase tracking-wider ${
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
        <p className="text-sm font-medium text-slate-300 min-h-12 leading-relaxed">
          {actionObj ? actionObj.action : agency.action}
        </p>
        
        <div className="mt-5 flex items-end justify-between">
          <div className="flex flex-col">
            <span className="text-xs font-medium text-slate-500 uppercase tracking-wider mb-1">Response Time</span>
            <div className="text-xl font-mono font-bold">
              {isAcknowledged ? (
                <span className={isSlaMissed ? 'text-yellow-400' : 'text-green-400'}>
                  {String(Math.floor(responseTime / 60)).padStart(2, '0')}:
                  {String(responseTime % 60).padStart(2, '0')}
                </span>
              ) : (
                <span className="text-slate-300">--:--</span>
              )}
            </div>
          </div>
          
          <button
            onClick={() => onAcknowledge(agencyKey)}
            disabled={!alert || isAcknowledged}
            className={`px-5 py-2.5 rounded-lg font-bold text-sm tracking-wide transition-all z-10 ${
              !alert 
                ? 'bg-slate-800 text-slate-500 cursor-not-allowed' 
                : isAcknowledged 
                  ? 'bg-green-500/20 text-green-500 cursor-not-allowed border border-green-500/30'
                  : 'bg-red-600 hover:bg-red-500 text-white shadow-lg cursor-pointer transform hover:-translate-y-0.5 active:translate-y-0'
            }`}
          >
            {isAcknowledged ? 'ACKNOWLEDGED' : 'ACKNOWLEDGE'}
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
