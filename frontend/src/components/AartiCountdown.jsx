import React from 'react';

/**
 * S7 — AartiCountdown: Shows upcoming aarti timing with countdown.
 * Goes red during active aarti, amber during pre-surge window.
 */
const AartiCountdown = ({ aartiContext }) => {
  if (!aartiContext || (!aartiContext.aarti_active && !aartiContext.aarti_name)) {
    return null;
  }

  const { aarti_active, aarti_name, minutes_to_next, multiplier } = aartiContext;

  if (aarti_active) {
    return (
      <div className="flex items-center gap-2 px-3 py-2 rounded-lg bg-red-500/15 border border-red-500/30 animate-pulse">
        <span className="text-lg">🪔</span>
        <div className="flex flex-col">
          <span className="text-xs font-bold text-red-400 uppercase tracking-wider">
            {aarti_name} Aarti — ACTIVE
          </span>
          <span className="text-[10px] text-red-300/70">
            Pressure elevated ×{multiplier?.toFixed(2)}
          </span>
        </div>
      </div>
    );
  }

  if (aarti_name && minutes_to_next != null && minutes_to_next <= 15) {
    const urgency = minutes_to_next <= 5 ? 'text-amber-400 bg-amber-500/15 border-amber-500/30' 
                                          : 'text-yellow-400 bg-yellow-500/10 border-yellow-500/20';
    return (
      <div className={`flex items-center gap-2 px-3 py-2 rounded-lg border ${urgency}`}>
        <span className="text-lg">🪔</span>
        <div className="flex flex-col">
          <span className="text-xs font-bold uppercase tracking-wider">
            {aarti_name} Aarti in {minutes_to_next} min
          </span>
          <span className="text-[10px] opacity-70">
            Pre-surge — elevated pressure expected
          </span>
        </div>
      </div>
    );
  }

  return null;
};

export default AartiCountdown;
