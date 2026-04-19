import React from 'react';

/**
 * S8 — FlowDirectionIndicator: Shows bidirectional flow with counter-flow warnings.
 * Two arrows (↑ entry, ↓ exit) with live pax/min values. Red on counter-flow.
 */
const FlowDirectionIndicator = ({ entryFlow = 0, exitFlow = 0, counterFlowStatus = null }) => {
  const isCounterFlow = !!counterFlowStatus;
  const isCritical = counterFlowStatus?.includes('CRITICAL');
  const isWarning = counterFlowStatus?.includes('WARNING');

  const borderColor = isCritical ? 'border-red-500/40' 
                    : isWarning ? 'border-amber-500/30' 
                    : 'border-slate-700/50';
  const bgColor = isCritical ? 'bg-red-500/10' 
                : isWarning ? 'bg-amber-500/5' 
                : 'bg-slate-800/30';

  return (
    <div className={`rounded-lg border ${borderColor} ${bgColor} p-3`}>
      <div className="flex items-center justify-between mb-2">
        <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider">
          Flow Direction
        </span>
        {isCounterFlow && (
          <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded ${
            isCritical ? 'bg-red-500/20 text-red-400 animate-pulse' : 'bg-amber-500/15 text-amber-400'
          }`}>
            ⚠ Counter-Flow
          </span>
        )}
      </div>

      <div className="flex items-center justify-between gap-4">
        {/* Entry Flow */}
        <div className="flex items-center gap-2">
          <div className={`w-8 h-8 rounded-full flex items-center justify-center text-lg ${
            isCritical ? 'bg-red-500/20' : 'bg-blue-500/15'
          }`}>
            ↑
          </div>
          <div className="flex flex-col">
            <span className="text-xs text-slate-500">Entry</span>
            <span className={`text-sm font-bold tabular-nums ${
              isCritical ? 'text-red-400' : 'text-blue-400'
            }`}>
              {entryFlow?.toFixed(0)} <span className="text-[10px] text-slate-600">pax/min</span>
            </span>
          </div>
        </div>

        {/* Divider with flow indicator */}
        <div className="flex flex-col items-center">
          <div className={`h-0.5 w-12 ${isCritical ? 'bg-red-500' : isWarning ? 'bg-amber-500' : 'bg-slate-700'}`}></div>
          {isCounterFlow && (
            <span className="text-[9px] text-red-400 mt-1">SQUEEZE</span>
          )}
        </div>

        {/* Exit Flow */}
        <div className="flex items-center gap-2">
          <div className="flex flex-col items-end">
            <span className="text-xs text-slate-500">Exit</span>
            <span className={`text-sm font-bold tabular-nums ${
              isCritical ? 'text-red-400' : 'text-green-400'
            }`}>
              {exitFlow?.toFixed(0)} <span className="text-[10px] text-slate-600">pax/min</span>
            </span>
          </div>
          <div className={`w-8 h-8 rounded-full flex items-center justify-center text-lg ${
            isCritical ? 'bg-red-500/20' : 'bg-green-500/15'
          }`}>
            ↓
          </div>
        </div>
      </div>

      {isCritical && (
        <div className="mt-2 px-2 py-1 bg-red-500/10 rounded text-[10px] text-red-300 text-center">
          Entry/exit collision risk — implement one-way flow immediately
        </div>
      )}
    </div>
  );
};

export default FlowDirectionIndicator;
