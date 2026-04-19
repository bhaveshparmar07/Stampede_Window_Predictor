import React from 'react';

/**
 * S4 — TollIndicatorStrip: Visual strip showing toll booth surge status + ETA.
 * Shows all toll booths feeding the active corridor with surge ratio bars.
 */
const TollIndicatorStrip = ({ tollStatus = [] }) => {
  if (!tollStatus || tollStatus.length === 0) return null;

  return (
    <div className="bg-slate-800/40 border border-slate-700/50 rounded-lg p-3">
      <div className="flex items-center gap-2 mb-2">
        <span className="text-sm">🛣️</span>
        <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider">
          Toll Booth Indicators
        </span>
      </div>

      <div className="space-y-2">
        {tollStatus.map((toll, i) => {
          const ratio = toll.surge_ratio || 1;
          const tierColor = toll.tier === 'PRE_ARRIVAL_WARNING' ? '#ef4444'
                          : toll.tier === 'ELEVATED_WATCH' ? '#eab308'
                          : '#22c55e';
          const barWidth = Math.min(ratio / 4 * 100, 100);

          return (
            <div key={toll.booth_id || i} className="flex items-center gap-3">
              {/* Booth label */}
              <div className="flex flex-col min-w-[80px]">
                <span className="text-[10px] text-slate-400 font-medium truncate">
                  {toll.highway || toll.booth_id}
                </span>
                <span className="text-[9px] text-slate-600">
                  ETA {toll.eta_min}m → {toll.target_corridor}
                </span>
              </div>

              {/* Surge bar */}
              <div className="flex-1 h-4 bg-slate-900 rounded-full overflow-hidden relative">
                <div
                  className="h-full rounded-full transition-all duration-500"
                  style={{ width: `${barWidth}%`, backgroundColor: tierColor }}
                />
                <span className="absolute inset-0 flex items-center justify-center text-[9px] font-bold text-white/80">
                  {ratio.toFixed(1)}×
                </span>
              </div>

              {/* Alert tier badge */}
              {toll.tier !== 'NORMAL' && (
                <span
                  className="text-[9px] font-bold px-1.5 py-0.5 rounded whitespace-nowrap"
                  style={{ backgroundColor: `${tierColor}20`, color: tierColor }}
                >
                  {toll.tier === 'PRE_ARRIVAL_WARNING' ? '⚠ SURGE' : '● WATCH'}
                </span>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default TollIndicatorStrip;
