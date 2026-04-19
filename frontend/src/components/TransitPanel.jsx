import React from 'react';

/**
 * S3 — TransitPanel: Shows incoming bus convoy status with projected pressure + ETA.
 */
const TransitPanel = ({ transitStatus = {} }) => {
  const corridors = Object.entries(transitStatus);
  if (corridors.length === 0) return null;

  return (
    <div className="bg-slate-800/40 border border-slate-700/50 rounded-lg p-3">
      <div className="flex items-center gap-2 mb-2">
        <span className="text-sm">🚌</span>
        <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider">
          In-Transit Convoy
        </span>
      </div>

      <div className="space-y-2">
        {corridors.map(([corridor, data]) => {
          if (!data || !data.vehicles_in_transit) return null;

          const tierColor = data.alert_tier === 'PRE_ARRIVAL_WARNING' ? '#ef4444'
                          : data.alert_tier === 'ELEVATED_WATCH' ? '#eab308'
                          : '#22c55e';

          return (
            <div key={corridor} className="flex items-center justify-between gap-2 bg-slate-900/40 rounded-md px-3 py-2">
              <div className="flex flex-col">
                <span className="text-xs font-bold text-white">→ {corridor}</span>
                <span className="text-[10px] text-slate-500">
                  {data.vehicles_in_transit} buses · {data.projected_pax || '—'} pax
                </span>
              </div>

              <div className="flex items-center gap-3">
                {/* ETA */}
                <div className="flex flex-col items-center">
                  <span className="text-[9px] text-slate-600 uppercase">ETA</span>
                  <span className="text-sm font-bold tabular-nums text-white">
                    {data.eta_min?.toFixed(0)}m
                  </span>
                </div>

                {/* Projected pressure */}
                <div className="flex flex-col items-center min-w-[48px]">
                  <span className="text-[9px] text-slate-600 uppercase">Proj.</span>
                  <span className="text-sm font-black tabular-nums" style={{ color: tierColor }}>
                    {data.projected_pressure_index?.toFixed(0)}
                  </span>
                </div>

                {/* Tier badge */}
                {data.alert_tier !== 'NORMAL' && (
                  <span
                    className="text-[9px] font-bold px-1.5 py-0.5 rounded whitespace-nowrap"
                    style={{ backgroundColor: `${tierColor}20`, color: tierColor }}
                  >
                    {data.alert_tier === 'PRE_ARRIVAL_WARNING' ? '⚠ INCOMING' : '● WATCH'}
                  </span>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default TransitPanel;
