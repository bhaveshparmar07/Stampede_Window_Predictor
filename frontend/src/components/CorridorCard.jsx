import React from 'react';
import { Activity, Users, ArrowRightToLine, ArrowLeftFromLine } from 'lucide-react';
import { PRESSURE_THRESHOLDS } from '../utils/constants';

const CorridorCard = ({ 
  location, 
  pressureIndex, 
  riskLevel,
  entryFlow,
  exitFlow,
  isActive = false,
  onClick
}) => {
  // Determine color based on threshold
  let colorObj = PRESSURE_THRESHOLDS.safe;
  if (pressureIndex >= PRESSURE_THRESHOLDS.watch.min) colorObj = PRESSURE_THRESHOLDS.watch;
  if (pressureIndex >= PRESSURE_THRESHOLDS.critical.min) colorObj = PRESSURE_THRESHOLDS.critical;

  return (
    <div 
      onClick={onClick}
      className={`relative cursor-pointer rounded-xl overflow-hidden transition-all duration-200 border-2 ${
        isActive 
          ? 'bg-slate-800 scale-[1.02] shadow-lg shadow-black/20' 
          : 'bg-slate-900/40 border-slate-800/50 hover:bg-slate-800/80'
      }`}
      style={{
        borderColor: isActive ? colorObj.color : undefined
      }}
    >
      <div className="p-4 flex flex-col h-full">
        <div className="flex justify-between items-start mb-3">
          <h3 className="font-bold text-lg text-white">{location}</h3>
          
          {/* Risk Badge */}
          <div 
            className="px-2 py-0.5 rounded text-xs font-bold uppercase tracking-wider"
            style={{ backgroundColor: `${colorObj.color}20`, color: colorObj.color }}
          >
            {colorObj.label}
          </div>
        </div>

        <div className="flex items-center justify-between mt-auto">
          {/* Pressure Score */}
          <div className="flex flex-col">
            <span className="text-xs text-slate-500 font-medium uppercase tracking-wider bg-slate-900/50 px-1.5 py-0.5 rounded mr-auto">Index</span>
            <div className="flex items-end space-x-1">
              <span className="text-3xl font-black tabular-nums tracking-tighter" style={{ color: colorObj.color }}>
                {pressureIndex?.toFixed(0) || 0}
              </span>
              <span className="text-xs text-slate-500 font-bold pb-1 bg-slate-900/50 px-1 rounded-sm">/ 100</span>
            </div>
          </div>
          
          {/* Flow Mini-Stats */}
          <div className="flex flex-col items-end space-y-1">
            <div className="flex items-center space-x-1.5 text-xs font-medium bg-slate-900/50 px-2 py-1 rounded-md border border-slate-800">
              <span className="text-slate-500 w-8">IN</span>
              <span className="text-blue-400 tabular-nums font-bold w-6 text-right">{entryFlow?.toFixed(0) || 0}</span>
            </div>
            <div className="flex items-center space-x-1.5 text-xs font-medium bg-slate-900/50 px-2 py-1 rounded-md border border-slate-800">
              <span className="text-slate-500 w-8">OUT</span>
              <span className="text-green-400 tabular-nums font-bold w-6 text-right">{exitFlow?.toFixed(0) || 0}</span>
            </div>
          </div>
        </div>
      </div>
      
      {/* Active Indicator Bar */}
      {isActive && (
        <div 
          className="absolute left-0 bottom-0 top-0 w-1.5" 
          style={{ backgroundColor: colorObj.color }}
        />
      )}
    </div>
  );
};

export default CorridorCard;
