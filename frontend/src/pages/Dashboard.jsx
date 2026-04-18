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
import { AGENCIES } from '../utils/constants';

const Dashboard = () => {
  const wsData = useWebSocket();
  const { pressure, predictions, alerts, classifications, flow_rates, flow_history, locations } = wsData;
  
  // By default, select the first location or 'Ambaji'
  const [activeLocation, setActiveLocation] = useState('Ambaji');
  
  // Make sure activeLocation is valid once we get locations
  useEffect(() => {
    if (locations.length > 0 && !locations.includes(activeLocation)) {
      setActiveLocation(locations[0]);
    }
  }, [locations, activeLocation]);

  // Find active alert for current location
  const activeAlert = alerts?.find(a => a.status === 'active' && a.location === activeLocation) || null;

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

  return (
    <div className="p-6 h-full flex flex-col">
      {/* Active Alert Banner */}
      <AlertBanner alert={activeAlert} currentPressure={currentPressure} />

      <div className="grid grid-cols-12 gap-6 flex-1 min-h-0">
        
        {/* Left Column: List of Corridors */}
        <div className="col-span-12 xl:col-span-3 flex flex-col space-y-4 overflow-y-auto pr-2 pb-4">
          <h2 className="text-sm font-bold text-slate-500 uppercase tracking-wider mb-2">Monitored Corridors</h2>
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
