import React from 'react';
import PressureGauge from '../PressureGauge';

export default function StadiumCenterPanel({
  activeLocation,
  venueType,
  currentPressure,
  readings,
  correlationSignal
}) {
  const matchStatus = readings?.match_status || "Unknown";
  const attendance = readings?.expected_attendance || readings?.estimated_attendance || 0;
  const dispatchEta = readings?.dispersal_wave_ETA || 0;

  let emoji = "🏟"; 
  let primaryLabel = "Venue Fill";
  if (venueType === 'procession') { emoji = "🚩"; primaryLabel = "Route Congestion"; }
  else if (venueType === 'strike') { emoji = "🚧"; primaryLabel = "Zone Compression"; }
  else if (venueType === 'social' || venueType === 'mela') { emoji = "🎪"; primaryLabel = "Area Density"; }
  else if (venueType === 'rally') { emoji = "📢"; primaryLabel = "Perimeter Density"; }

  const renderSpecifics = () => {
    if (venueType === 'procession') {
      return (
        <>
          <div className="bg-slate-900 border border-slate-800 p-4 rounded-lg text-center">
            <div className="text-2xl font-black text-amber-500">{readings?.route_progress_pct || 0}%</div>
            <div className="text-[10px] text-slate-500 uppercase tracking-widest mt-1">Route Progress</div>
          </div>
          <div className="bg-slate-900 border border-slate-800 p-4 rounded-lg text-center">
            <div className="text-2xl font-black text-purple-400">{readings?.next_junction_ETA || 0} min</div>
            <div className="text-[10px] text-slate-500 uppercase tracking-widest mt-1">Next Jct ETA</div>
          </div>
        </>
      );
    }
    if (venueType === 'strike') {
      return (
        <>
          <div className="bg-slate-900 border border-slate-800 p-4 rounded-lg text-center w-full">
            <div className="text-xl font-black text-orange-500">{readings?.blocked_routes || "NH947/SH41"}</div>
            <div className="text-[10px] text-slate-500 uppercase tracking-widest mt-1">Blocked Routes</div>
          </div>
          <div className="bg-slate-900 border border-slate-800 p-4 rounded-lg text-center">
            <div className="text-2xl font-black text-orange-400">{readings?.ETA_clearance || "Unknown"}</div>
            <div className="text-[10px] text-slate-500 uppercase tracking-widest mt-1">ETA Clearance</div>
          </div>
        </>
      );
    }
    // Default (Stadium/Rally/Social)
    return (
      <>
        <div className="bg-slate-900 border border-slate-800 p-4 rounded-lg text-center">
          <div className="text-3xl font-black text-amber-500">{attendance.toLocaleString()}</div>
          <div className="text-[10px] text-slate-500 uppercase tracking-widest mt-1">Est. Attendance</div>
        </div>
        <div className="bg-slate-900 border border-slate-800 p-4 rounded-lg text-center">
          <div className="text-2xl font-black text-blue-400">{dispatchEta} min</div>
          <div className="text-[10px] text-slate-500 uppercase tracking-widest mt-1">Dispersal Wave ETA</div>
        </div>
      </>
    );
  };

  return (
    <div className="col-span-12 lg:col-span-6 xl:col-span-5 flex flex-col space-y-6">
      <div className="bg-slate-950 border border-slate-800 rounded-xl p-6 shadow-xl flex flex-col items-center">
        <div className="flex w-full items-center justify-between border-b border-slate-800 pb-4 mb-6">
          <h2 className="text-xl font-bold text-white tracking-wide uppercase">
            {emoji} {activeLocation}
          </h2>
          <span className={`text-xs px-2 py-1 rounded font-bold uppercase ${matchStatus === 'ended' ? 'bg-red-500/20 text-red-400' : 'bg-green-500/20 text-green-400'}`}>
            {venueType === 'procession' ? 'EN ROUTE' : (venueType === 'strike' ? 'ACTIVE' : matchStatus)}
          </span>
        </div>
        
        <div className="flex flex-col md:flex-row items-center justify-around w-full gap-8">
          <div className="flex flex-col items-center">
            <h3 className="text-sm font-medium text-slate-500 uppercase mb-2">{primaryLabel}</h3>
            <PressureGauge value={currentPressure} size="lg" />
          </div>
          <div className="flex flex-col gap-4 w-full md:w-auto">
            {renderSpecifics()}
          </div>
        </div>
      </div>

      {correlationSignal && correlationSignal.compound_mult > 1.0 && (
        <div className="bg-indigo-950/30 border border-indigo-500/30 rounded-xl p-6 shadow-xl">
          <h2 className="text-sm font-bold text-indigo-400 uppercase tracking-wider mb-4 flex items-center gap-2">
            <span>⚡</span> Regional Correlation Active
          </h2>
          <p className="text-sm text-indigo-200/80 mb-2">
            This event is currently generating crowd waves impacting nearby monitored facilities.
          </p>
          <div className="flex items-center gap-4 mt-4">
            <div className="bg-indigo-900/50 p-3 rounded flex-1 text-center">
              <div className="text-xl font-bold text-white">+{Math.round((correlationSignal.compound_mult - 1) * 100)}%</div>
              <div className="text-[10px] text-indigo-300 uppercase">Pressure Multiplier</div>
            </div>
            <div className="bg-indigo-900/50 p-3 rounded flex-1 text-center">
              <div className="text-xl font-bold text-white">{correlationSignal.active_signal_count}</div>
              <div className="text-[10px] text-indigo-300 uppercase">Active Signals</div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
