import React from 'react';
import { PRESSURE_THRESHOLDS } from '../utils/constants';
import { MoveRight, MoveLeft } from 'lucide-react';
import { useTheme } from '../context/ThemeContext';

/**
 * CorridorCard - Optimized for vertical stacking in narrow sidebars.
 * Prevents "squished" appearance by managing vertical spacing and pill density.
 */
const CorridorCard = ({ 
  location, 
  pressureIndex, 
  entryFlow,
  exitFlow,
  isActive = false,
  onClick,
  aartiContext,
  clusterData,
  processionStatus,
}) => {
  const { isDarkMode } = useTheme();
  
  // Determine color based on threshold
  let colorObj = PRESSURE_THRESHOLDS.safe;
  if (pressureIndex >= PRESSURE_THRESHOLDS.watch.min) colorObj = PRESSURE_THRESHOLDS.watch;
  if (pressureIndex >= PRESSURE_THRESHOLDS.critical.min) colorObj = PRESSURE_THRESHOLDS.critical;

  return (
    <div 
      onClick={onClick}
      className={`relative cursor-pointer rounded-xl overflow-hidden transition-all duration-300 border-2 min-h-[160px] flex flex-col ${
        isActive 
          ? (isDarkMode ? 'bg-slate-800 shadow-2xl scale-[1.02]' : 'bg-white shadow-xl scale-[1.02] border-blue-200')
          : (isDarkMode ? 'bg-slate-900/40 border-slate-800/50 hover:bg-slate-800/80 shadow-inner' : 'bg-white border-slate-100 hover:border-slate-200 hover:shadow-sm')
      }`}
      style={{
        borderColor: isActive ? colorObj.color : undefined
      }}
    >
      {/* Background Gradient for Active Risk */}
      {isActive && (
        <div 
          className="absolute inset-0 opacity-[0.05] pointer-events-none"
          style={{ background: `linear-gradient(to right, ${colorObj.color}, transparent)` }}
        />
      )}

      {/* Main Content Container with optimized spacing */}
      <div className="pt-4 px-4 pb-4 flex flex-col flex-1 relative z-10 w-full">
        {/* Header: Title and Status Badge */}
        <div className="flex justify-between items-start mb-2">
          <div className="flex flex-col min-w-0 flex-1 mr-2">
            <h3 className={`font-black text-lg tracking-tight leading-none truncate ${isDarkMode ? 'text-white' : 'text-slate-900'}`}>
              {location}
            </h3>
            <span className="text-[9px] uppercase font-bold tracking-widest text-slate-500 mt-1">Corridor</span>
          </div>
          
          <div 
            className="px-2 py-0.5 rounded-full text-[9px] font-black uppercase tracking-widest shadow-sm shrink-0 border whitespace-nowrap"
            style={{ 
              backgroundColor: `${colorObj.color}15`, 
              color: colorObj.color, 
              borderColor: `${colorObj.color}30` 
            }}
          >
            {colorObj.label}
          </div>
        </div>

        {/* Indicators Row (Simplified for narrow view) */}
        <div className="flex flex-wrap gap-1 mb-2">
          {aartiContext?.aarti_active && (
            <span className="text-[8px] px-1.5 py-0.5 rounded bg-red-500/10 text-red-500 font-black border border-red-500/20">
               🪔 Aarti
            </span>
          )}
          {processionStatus?.active && (
            <span className="text-[8px] px-1.5 py-0.5 rounded bg-orange-500/10 text-orange-500 font-black border border-orange-500/10">
               🚩 {processionStatus.block_pct}%
            </span>
          )}
          {clusterData?.cluster_flag && (
            <span className={`text-[8px] px-1.5 py-0.5 rounded font-black border ${
              clusterData.cluster_severity === 'critical' ? 'bg-red-500/10 text-red-500' : 'bg-amber-500/10 text-amber-500'
            }`}>
               ⬤ Cluster
            </span>
          )}
        </div>

        {/* Statistics Row: Pushed to bottom with mt-auto */}
        <div className={`flex items-end justify-between mt-auto pt-3 border-t ${isDarkMode ? 'border-slate-800/20' : 'border-slate-50'}`}>
          {/* Pressure Score HERO */}
          <div className="flex flex-col shrink-0">
            <div className="flex items-baseline leading-none">
              <span className="text-4xl font-black tabular-nums tracking-tighter" style={{ color: colorObj.color }}>
                {Math.round(Number(pressureIndex) || 0)}
              </span>
              <span className={`text-[10px] font-bold opacity-30 ml-0.5 ${isDarkMode ? 'text-white' : 'text-slate-900'}`}>/100</span>
            </div>
            <span className="text-[8px] font-black uppercase tracking-widest mt-1 text-slate-500/80">Pressure Index</span>
          </div>
          
          {/* Flow Vertical Pill (Vertical-first for narrow cards) */}
          <div className={`flex flex-col p-1 rounded-lg shrink-0 ${isDarkMode ? 'bg-slate-950/80 border border-slate-800/40' : 'bg-slate-50 border border-slate-100'}`}>
            <div className="flex items-center gap-1.5 px-1.5 py-0.5">
              <MoveRight size={10} className="text-blue-500" />
              <span className={`text-[11px] font-black tabular-nums ${isDarkMode ? 'text-slate-200' : 'text-slate-600'}`}>
                {Math.round(Number(entryFlow) || 0)}
              </span>
            </div>
            <div className={`h-px mx-1 my-0.5 ${isDarkMode ? 'bg-slate-800' : 'bg-slate-200'}`} />
            <div className="flex items-center gap-1.5 px-1.5 py-0.5">
              <MoveLeft size={10} className="text-green-500" />
              <span className={`text-[11px] font-black tabular-nums ${isDarkMode ? 'text-slate-200' : 'text-slate-600'}`}>
                {Math.round(Number(exitFlow) || 0)}
              </span>
            </div>
          </div>
        </div>
      </div>
      
      {/* Selection Indicator Bar (Active State) */}
      {isActive && (
        <div 
          className="absolute left-0 bottom-0 top-0 w-1" 
          style={{ backgroundColor: colorObj.color }}
        />
      )}
    </div>
  );
};

export default CorridorCard;
