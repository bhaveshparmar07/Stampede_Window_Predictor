import React, { useState, useEffect } from 'react';
import { useWebSocket } from '../hooks/useWebSocket';
import { acknowledgeAlert } from '../utils/api';
import PressureGauge from '../components/PressureGauge';
import CrushCountdown from '../components/CrushCountdown';
import SurgeClassifier from '../components/SurgeClassifier';
import AlertBanner from '../components/AlertBanner';
import AgencyPanel from '../components/AgencyPanel';
import FlowChart from '../components/FlowChart';
import CorridorMap from '../components/CorridorMap';
import TempleCenterPanel from '../components/panels/TempleCenterPanel';
import StadiumCenterPanel from '../components/panels/StadiumCenterPanel';
// Scenario extension components
import AartiCountdown from '../components/AartiCountdown';
import FlowDirectionIndicator from '../components/FlowDirectionIndicator';
import TollIndicatorStrip from '../components/TollIndicatorStrip';
import { EventContextBadge, CalendarContextPill } from '../components/EventContextBadge';
import BlackSwanPanel from '../components/BlackSwanPanel';
import TransitPanel from '../components/TransitPanel';
import { AGENCIES, API_BASE_URL } from '../utils/constants';
import { useTheme } from '../context/ThemeContext';

const Dashboard = () => {
  const wsData = useWebSocket();
  const { isDarkMode } = useTheme();
  const { 
    pressure, predictions, alerts, classifications, flow_rates, flow_history, locations,
    // Scenario data
    aarti_context, calendar_context, event_context, auspicious_context,
    procession_status, anomaly_data, counter_flow, cluster_data,
    toll_status, transit_status, zone_status,
    venue_readings, correlation_signals,
    isConnected,
  } = wsData;
  
  // By default, select the first location or 'Ambaji'
  const [activeLocation, setActiveLocation] = useState('Ambaji');
  const [smsToast, setSmsToast] = useState(null);
  const [locationRegistry, setLocationRegistry] = useState({ temples: [], events: [] });
  
  useEffect(() => {
    const normalizeRegistry = (data) => ({
      temples: Array.isArray(data?.temples) ? data.temples : [],
      events: Array.isArray(data?.events) ? data.events : [],
    });
    const fetchLocs = () => {
      fetch(`${API_BASE_URL}/api/locations`)
        .then(async (res) => {
          if (!res.ok) throw new Error(`locations ${res.status}`);
          return res.json();
        })
        .then((data) => setLocationRegistry(normalizeRegistry(data)))
        .catch((err) => {
          console.error('Could not load location registry', err);
          setLocationRegistry({ temples: [], events: [] });
        });
    };
    fetchLocs();
    const intv = setInterval(fetchLocs, 3000); // refresh every 3 seconds for dynamically discovered events
    return () => clearInterval(intv);
  }, []);

  // Make sure activeLocation is valid once we get locations
  useEffect(() => {
    const validLocations = [
      ...locations, 
      ...locationRegistry.temples.map(t => t.id), 
      ...locationRegistry.temples.map(t => t.name), 
      ...locationRegistry.events.map(e => e.id)
    ];
    if (locations.length > 0 && !validLocations.includes(activeLocation)) {
      setActiveLocation(locations[0]);
    }
  }, [locations, activeLocation, locationRegistry]);

  // Find active alert for current location
  const activeAlert = alerts?.find(a => a.status === 'active' && a.location === activeLocation) || null;
  useEffect(() => {
    if (activeAlert?.sms_sent) {
      setSmsToast(`SMS escalation sent for ${activeAlert.location}`);
      const t = setTimeout(() => setSmsToast(null), 4000);
      return () => clearTimeout(t);
    }
  }, [activeAlert?.id, activeAlert?.sms_sent]);

  // Handle Acknowledge
  const handleAcknowledge = async (agencyKey) => {
    if (!activeAlert) return;
    try {
      await acknowledgeAlert(activeAlert.id, agencyKey);
      // Response processed by websocket broadcast
    } catch (error) {
      console.error('Error acknowledging alert:', error);
    }
  };

  // If no data yet, show loading
  if (!wsData.timestamp && locations.length === 0) {
    return (
      <div className="h-full flex items-center justify-center">
        <div className="flex flex-col items-center space-y-4">
          <div className="w-16 h-16 border-4 border-slate-700 border-t-blue-500 rounded-full animate-spin"></div>
          <p className="text-slate-500 font-medium">Waiting for ingestion stream...</p>
          <p className="text-xs text-slate-500">Run `python simulation/stream_data.py --speed 2`</p>
        </div>
      </div>
    );
  }

  const currentPressure = pressure[activeLocation] || 0;
  const currentPrediction = predictions[activeLocation] || { crush_window_min: 15, risk_level: 'Low' };
  const currentClassification = classifications[activeLocation] || 'MONITORING';
  const currentFlowHistory = flow_history[activeLocation] || [];
  
  // Scenario context for active location
  const locAarti = aarti_context?.[activeLocation] || {};
  const locCalendar = calendar_context?.[activeLocation] || {};
  const locEvent = event_context?.[activeLocation] || {};
  const locAuspicious = auspicious_context?.[activeLocation] || {};
  const locProcession = procession_status?.[activeLocation] || {};
  const locAnomaly = anomaly_data?.[activeLocation] || {};
  const locCounterFlow = counter_flow?.[activeLocation] || null;
  const locCluster = cluster_data?.[activeLocation] || {};
  const entryFlow = flow_rates?.[activeLocation]?.entry || 0;
  const exitFlow = flow_rates?.[activeLocation]?.exit || 0;

  // Filter toll status for active corridor
  const corridorTolls = (toll_status || []).filter(t => t.target_corridor === activeLocation);

  // Find venue type from registry
  const locDef = [...(locationRegistry.temples || []), ...(locationRegistry.events || [])].find(
    (l) => l.name === activeLocation || l.id === activeLocation
  );
  const venueType = locDef?.venue_type || 'temple';

  // Split locations into permanent temples vs dynamic events for the sidebar
  const templeLocations = locations.filter((locName) => {
    const lDef = [...(locationRegistry.temples || [])].find((l) => l.name === locName || l.id === locName);
    return lDef || !(locationRegistry.events || []).find((e) => e.name === locName || e.id === locName);
  });

  const eventLocations = locationRegistry.events || [];

  return (
    <div className={`p-6 h-full flex flex-col transition-colors duration-300 ${isDarkMode ? 'bg-slate-900' : 'bg-slate-50'}`}>
      {smsToast && (
        <div className="mb-4 bg-indigo-600/20 border border-indigo-500/30 text-indigo-200 px-4 py-2 rounded-lg text-sm font-semibold">
          {smsToast}
        </div>
      )}
      {/* Connection Status */}
      <div className="flex items-center gap-2 mb-2">
        <div className={`w-2 h-2 rounded-full ${isConnected ? 'bg-green-500' : 'bg-red-500 animate-pulse'}`}></div>
        <span className="text-[10px] text-slate-600 font-medium">
          {isConnected ? 'LIVE' : 'RECONNECTING...'}
        </span>
      </div>

      {/* Active Alert Banner */}
      <AlertBanner alert={activeAlert} currentPressure={currentPressure} />

      {/* Procession Warning Banner */}
      {locProcession?.active && (
        <div className="mb-4 px-4 py-2 rounded-lg bg-orange-500/10 border border-orange-500/30 flex items-center gap-3 animate-pulse">
          <span className="text-lg">🚩</span>
          <div>
            <span className="text-xs font-black text-orange-400 uppercase">
              PROCESSION ACTIVE — {locProcession.name}
            </span>
            <span className="text-[10px] text-orange-300/60 ml-2">
              Corridor {locProcession.block_pct}% blocked
              {locProcession.remaining_min != null && ` · ${locProcession.remaining_min}m remaining`}
            </span>
          </div>
        </div>
      )}

      <div className="grid grid-cols-12 gap-6 flex-1 min-h-0">
        
        {/* Left Column: List of Corridors + Context Badges */}
        <div className="col-span-12 xl:col-span-3 flex flex-col space-y-4 overflow-y-auto pr-2 pb-4">
          <h2 className="text-[11px] font-bold text-slate-500 uppercase tracking-wider mb-2 pt-2">Monitored Corridors</h2>
          
          {/* Monitored Temples Section */}
          <h3 className="text-[10px] font-black text-slate-500/70 uppercase tracking-widest mb-3 px-1 mt-2">Monitored Temples</h3>
          {templeLocations.length > 0 ? templeLocations.map(loc => {
            const isAct = activeLocation === loc;
            const eventPressure = pressure[loc] || 0;
            const rLevel = predictions[loc]?.risk_level || 'Low';
            
            let badgeText = "SAFE";
            let bgStr = "bg-green-500/10"; let textStr = "text-green-400"; let borderStr = "border-green-500/20"; let ringStr = "ring-green-500/30"; let shadowStr = "shadow-[0_0_20px_rgba(34,197,94,0.15)]"; let gradStr = "from-green-500/10";
            
            if (rLevel === "Moderate") { 
               badgeText = "WATCH"; 
               bgStr = "bg-amber-500/10"; textStr = "text-amber-400"; borderStr = "border-amber-500/20"; ringStr = "ring-amber-500/30"; shadowStr = "shadow-[0_0_20px_rgba(245,158,11,0.15)]"; gradStr = "from-amber-500/10";
            } else if (rLevel === "High" || rLevel === "Critical") { 
               badgeText = "CRITICAL"; 
               bgStr = "bg-red-500/10"; textStr = "text-red-400"; borderStr = "border-red-500/20"; ringStr = "ring-red-500/30"; shadowStr = "shadow-[0_0_20px_rgba(239,68,68,0.20)]"; gradStr = "from-red-500/10";
            }
            
            const numSignals = activeAlert && activeAlert.location === loc ? 1 : 0;

            return (
               <div 
                 key={loc}
                 onClick={() => setActiveLocation(loc)}
                 className={`relative overflow-hidden cursor-pointer rounded-xl p-3.5 mb-2.5 transition-all duration-300 border backdrop-blur-sm ${isAct ? `bg-slate-800/80 border-slate-700 ring-1 ring-inset ${ringStr} ${shadowStr}` : 'bg-slate-900/40 border-slate-800/50 hover:bg-slate-800/60 hover:border-slate-700/60'}`}
               >
                 {isAct && <div className={`absolute -top-10 -right-10 w-32 h-32 bg-gradient-radial ${gradStr} to-transparent rounded-full blur-2xl pointer-events-none opacity-60`}></div>}
                 
                 <div className="relative z-10 flex justify-between items-center">
                   <div className="flex-1 min-w-0 pr-3">
                     <div className="text-slate-100 font-bold text-[14px] tracking-wide">{loc}</div>
                     <div className="flex gap-2 items-center mt-1.5">
                       <span className={`px-1.5 py-0.5 rounded ${bgStr} ${textStr} ${borderStr} border text-[8.5px] font-black tracking-widest leading-none uppercase`}>{badgeText}</span>
                       <span className="text-[10px] font-medium text-slate-500 truncate mt-px">
                         {pressure[loc] ? `Risk: ${rLevel}` : "Awaiting sync"}
                       </span>
                     </div>
                   </div>
                   
                   <div className="flex flex-col items-end justify-center pl-2">
                     {pressure[loc] ? (
                       <span className={`text-[19px] font-black ${textStr} tabular-nums tracking-tighter leading-none`}>{Math.round(eventPressure)}</span>
                     ) : (
                       <div className="w-4 h-4 border-2 border-slate-700 border-t-slate-400 rounded-full animate-spin"></div>
                     )}
                     {numSignals > 0 && <div className="text-[9px] text-red-400 font-bold tracking-wider mt-1 px-1 bg-red-500/10 rounded">{numSignals} SIGNAL</div>}
                   </div>
                 </div>
               </div>
            );
          }) : (
            <div className="p-4 bg-slate-900/40 border border-slate-800/50 rounded-xl text-xs text-slate-500 text-center uppercase tracking-widest font-medium">No temples mapped</div>
          )}

          {/* Active Events Section */}
          {eventLocations.length > 0 && (
            <>
              <div className="h-px w-full bg-gradient-to-r from-transparent via-slate-800 to-transparent my-4"></div>
              <h3 className="text-[10px] font-black text-slate-500/70 uppercase tracking-widest mb-3 px-1">Dynamic Events ({eventLocations.length})</h3>
              
              <div className="space-y-2.5">
              {eventLocations.map(ev => {
                const locId = ev.id;
                const isAct = activeLocation === locId;
                const eventPressure = pressure[locId];
                const riskLevel = predictions[locId]?.risk_level || 'Low';

                let badgeText = "EVENT";
                let bgStr = "bg-blue-500/10"; let textStr = "text-blue-400"; let borderStr = "border-blue-500/20"; let ringStr = "ring-blue-500/30"; let shadowStr = "shadow-[0_0_20px_rgba(59,130,246,0.15)]"; let gradStr = "from-blue-500/10";
                
                if (ev.venue_type === 'stadium') { }
                else if (ev.venue_type === 'procession') { badgeText = "PROCESSION"; bgStr = "bg-purple-500/10"; textStr = "text-purple-400"; borderStr = "border-purple-500/20"; ringStr = "ring-purple-500/30"; shadowStr = "shadow-[0_0_20px_rgba(168,85,247,0.15)]"; gradStr = "from-purple-500/10"; }
                else if (ev.venue_type === 'social') { badgeText = "SOCIAL"; bgStr = "bg-amber-500/10"; textStr = "text-amber-400"; borderStr = "border-amber-500/20"; ringStr = "ring-amber-500/30"; shadowStr = "shadow-[0_0_20px_rgba(245,158,11,0.15)]"; gradStr = "from-amber-500/10"; }
                else if (ev.venue_type === 'strike') { badgeText = "STRIKE"; bgStr = "bg-orange-500/10"; textStr = "text-orange-400"; borderStr = "border-orange-500/20"; ringStr = "ring-orange-500/30"; shadowStr = "shadow-[0_0_20px_rgba(249,115,22,0.15)]"; gradStr = "from-orange-500/10"; }
                else if (ev.venue_type === 'mela') { badgeText = "MELA"; bgStr = "bg-emerald-500/10"; textStr = "text-emerald-400"; borderStr = "border-emerald-500/20"; ringStr = "ring-emerald-500/30"; shadowStr = "shadow-[0_0_20px_rgba(16,185,129,0.15)]"; gradStr = "from-emerald-500/10"; }
                else if (ev.venue_type === 'rally') { badgeText = "RALLY"; bgStr = "bg-rose-500/10"; textStr = "text-rose-400"; borderStr = "border-rose-500/20"; ringStr = "ring-rose-500/30"; shadowStr = "shadow-[0_0_20px_rgba(244,63,94,0.15)]"; gradStr = "from-rose-500/10"; }

                return (
                  <div 
                    key={locId} 
                    onClick={() => setActiveLocation(locId)}
                    className={`relative overflow-hidden cursor-pointer rounded-xl p-3 transition-all duration-300 border backdrop-blur-sm ${isAct ? `bg-slate-800/80 border-slate-700 ring-1 ring-inset ${ringStr} ${shadowStr}` : 'bg-slate-900/40 border-slate-800/50 hover:bg-slate-800/60 hover:border-slate-700/60'}`}
                  >
                    {isAct && <div className={`absolute -top-10 -right-10 w-32 h-32 bg-gradient-radial ${gradStr} to-transparent rounded-full blur-2xl pointer-events-none opacity-60`}></div>}
                    
                    <div className="relative z-10 flex justify-between items-center">
                      <div className="flex-1 min-w-0 pr-3">
                        <div className="text-slate-100 font-bold text-[13px] tracking-wide truncate">{ev.name}</div>
                        <div className="flex gap-2 items-center mt-1.5">
                          <span className={`px-1.5 py-0.5 rounded ${bgStr} ${textStr} border ${borderStr} text-[8.5px] font-black tracking-widest uppercase leading-none`}>{badgeText}</span>
                          <span className="text-[10px] font-medium text-slate-500 truncate mt-px">
                            {pressure[locId] ? `Risk: ${riskLevel}` : "Awaiting sync"}
                          </span>
                        </div>
                      </div>
                      
                      <div className="flex flex-col items-end justify-center pl-2">
                          {pressure[locId] ? (
                             <div className={`text-[17px] font-black ${textStr} tabular-nums tracking-tighter leading-none`}>{Math.round(eventPressure)}</div>
                          ) : (
                             <div className="w-4 h-4 border-2 border-slate-700 border-t-slate-400 rounded-full animate-spin"></div>
                          )}
                      </div>
                    </div>
                  </div>
                )
              })}
              </div>
            </>
          )}
        </div>

        {/* Middle Column: Gauges and Detail */}
        {venueType === 'temple' ? (
          <TempleCenterPanel 
            activeLocation={activeLocation}
            currentPressure={currentPressure}
            currentPrediction={currentPrediction}
            currentClassification={currentClassification}
            entryFlow={entryFlow}
            exitFlow={exitFlow}
            locCounterFlow={locCounterFlow}
            locAnomaly={locAnomaly}
            currentFlowHistory={currentFlowHistory}
          />
        ) : (
          <StadiumCenterPanel 
            activeLocation={locDef?.name || activeLocation}
            venueType={venueType}
            currentPressure={currentPressure}
            readings={venue_readings?.[activeLocation] || {}}
            correlationSignal={correlation_signals?.[activeLocation]}
          />
        )}

        {/* Right Column: Actions and Map */}
        <div className="col-span-12 lg:col-span-6 xl:col-span-4 flex flex-col space-y-6">
          
          <div className="h-64 rounded-xl overflow-hidden shadow-xl shrink-0">
            <CorridorMap 
              locations={locations} 
              activeLocation={activeLocation}
              pressureData={pressure} 
            />
          </div>
          
          <div className="flex-1 flex flex-col space-y-4">
            <h2 className="text-sm font-bold text-slate-500 uppercase tracking-wider mt-2">Agency Coordination Protocols</h2>
            
            <div className="flex-1 overflow-y-auto space-y-4 pr-1 pb-4">
              {Object.keys(AGENCIES).map(agencyKey => (
                <AgencyPanel 
                  key={agencyKey}
                  agencyKey={agencyKey}
                  alert={activeAlert}
                  onAcknowledge={handleAcknowledge}
                />
              ))}
            </div>
          </div>

        </div>

      </div>
    </div>
  );
};

export default Dashboard;
