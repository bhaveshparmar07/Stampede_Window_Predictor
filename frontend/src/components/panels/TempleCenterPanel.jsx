import React from 'react';
import PressureGauge from '../PressureGauge';
import CrushCountdown from '../CrushCountdown';
import SurgeClassifier from '../SurgeClassifier';
import FlowDirectionIndicator from '../FlowDirectionIndicator';
import BlackSwanPanel from '../BlackSwanPanel';
import FlowChart from '../FlowChart';

export default function TempleCenterPanel({ 
  activeLocation, 
  currentPressure, 
  currentPrediction, 
  currentClassification, 
  entryFlow, 
  exitFlow, 
  locCounterFlow, 
  locAnomaly, 
  currentFlowHistory 
}) {
  return (
    <div className="col-span-12 lg:col-span-6 xl:col-span-5 flex flex-col space-y-6">
      <div className="bg-slate-950 border border-slate-800 rounded-xl p-6 shadow-xl flex flex-col items-center">
        <h2 className="text-xl font-bold mb-6 text-white text-center w-full border-b border-slate-800 pb-4">
          {activeLocation} <span className="text-slate-500 font-medium">Corridor Pressure</span>
        </h2>
        
        <div className="flex flex-col md:flex-row items-center justify-around w-full gap-8">
          <PressureGauge value={currentPressure} size="lg" />
          <div className="w-full md:w-auto">
            <CrushCountdown 
              minutes={currentPrediction?.crush_window_min || 15} 
              isSafe={currentPrediction?.risk_level === 'Low' || currentPressure < 40}
            />
          </div>
        </div>
        
        <div className="w-full mt-8">
          <SurgeClassifier classification={currentClassification} />
        </div>
      </div>

      <FlowDirectionIndicator 
        entryFlow={entryFlow} 
        exitFlow={exitFlow} 
        counterFlowStatus={locCounterFlow} 
      />

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
  );
}
