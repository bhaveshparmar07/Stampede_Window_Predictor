import React, { useState, useEffect } from 'react';
import { useWebSocket } from '../hooks/useWebSocket';
import { acknowledgeAlert } from '../utils/api';
import PressureGauge from '../components/PressureGauge';
import CrushCountdown from '../components/CrushCountdown';
import SurgeClassifier from '../components/SurgeClassifier';
import AlertBanner from '../components/AlertBanner';
import AgencyPanel from '../components/AgencyPanel';
import FlowChart from '../components/FlowChart';
import CorridorCard from '../components/CorridorCard';
import CorridorMap from '../components/CorridorMap';
// Scenario extension components
import AartiCountdown from '../components/AartiCountdown';
import FlowDirectionIndicator from '../components/FlowDirectionIndicator';
import TollIndicatorStrip from '../components/TollIndicatorStrip';
import { EventContextBadge, CalendarContextPill } from '../components/EventContextBadge';
import BlackSwanPanel from '../components/BlackSwanPanel';
import TransitPanel from '../components/TransitPanel';
import ScenarioIntelligence from '../components/ScenarioIntelligence';
import { AGENCIES } from '../utils/constants';
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
    isConnected,
  } = wsData;
  
  // By default, select the first location or 'Ambaji'
  const [activeLocation, setActiveLocation] = useState('Ambaji');
  const [smsToast, setSmsToast] = useState(null);
  
  // Make sure activeLocation is valid once we get locations
  useEffect(() => {
    if (locations.length > 0 && !locations.includes(activeLocation)) {
      setActiveLocation(locations[0]);
    }
  }, [locations, activeLocation]);

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
          <h2 className="text-sm font-bold text-slate-500 uppercase tracking-wider mb-2">Monitored Corridors</h2>
          
          <ScenarioIntelligence 
            aartiContext={locAarti}
            calendarContext={locCalendar}
            eventContext={locEvent}
            auspiciousContext={locAuspicious}
            processionStatus={locProcession}
            anomalyData={locAnomaly}
            counterFlowStatus={locCounterFlow}
            clusterData={locCluster}
            tollStatus={corridorTolls}
            transitStatus={transit_status}
            zoneStatus={zone_status}
            entryFlow={entryFlow}
            exitFlow={exitFlow}
            location={activeLocation}
          />
          
          {/* Corridor Cards */}
          {locations.length > 0 ? locations.map(loc => (
            <CorridorCard 
              key={loc}
              location={loc}
              pressureIndex={pressure[loc]}
              riskLevel={predictions[loc]?.risk_level}
              entryFlow={flow_rates[loc]?.entry}
              exitFlow={flow_rates[loc]?.exit}
              isActive={activeLocation === loc}
              onClick={() => setActiveLocation(loc)}
              aartiContext={aarti_context?.[loc]}
              clusterData={cluster_data?.[loc]}
              processionStatus={procession_status?.[loc]}
            />
          )) : (
            <div className="p-4 bg-slate-800 rounded-lg text-sm text-slate-500 text-center">No locations mapped yet.</div>
          )}
        </div>

        {/* Middle Column: Gauges and Detail */}
        <div className="col-span-12 lg:col-span-6 xl:col-span-5 flex flex-col space-y-6">
          <div className="bg-slate-950 border border-slate-800 rounded-xl p-6 shadow-xl flex flex-col items-center">
            <h2 className="text-xl font-bold mb-6 text-white text-center w-full border-b border-slate-800 pb-4">
              {activeLocation} <span className="text-slate-500 font-medium">Pressure Index</span>
            </h2>
            
            <div className="flex flex-col md:flex-row items-center justify-around w-full gap-8">
              <PressureGauge value={currentPressure} size="lg" />
              <div className="w-full md:w-auto">
                <CrushCountdown 
                  minutes={currentPrediction.crush_window_min} 
                  isSafe={currentPrediction.risk_level === 'Low' || currentPressure < 40}
                />
              </div>
            </div>
            
            <div className="w-full mt-8">
              <SurgeClassifier classification={currentClassification} />
            </div>
          </div>

          {/* Flow Direction + Counter-flow Indicator */}
          <FlowDirectionIndicator 
            entryFlow={entryFlow} 
            exitFlow={exitFlow} 
            counterFlowStatus={locCounterFlow} 
          />

          {/* Black Swan / Anomaly Panel */}
          <BlackSwanPanel anomalyData={locAnomaly} location={activeLocation} />

          <div className="bg-slate-950 border border-slate-800 rounded-xl p-6 shadow-xl flex-1 flex flex-col min-h-[300px]">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-sm font-bold text-slate-500 uppercase tracking-wider">Live Flow Dynamics</h2>
              <div className="text-xs text-slate-500">Live 50 updates</div>
            </div>
            <div className="flex-1 min-h-0">
              <FlowChart data={currentFlowHistory} />
            </div>
          </div>
        </div>

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
