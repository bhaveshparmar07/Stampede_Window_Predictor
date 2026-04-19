import React from 'react';

/**
 * S1 — EventContextBadge: Amber banner when external event (IPL, mela) is active.
 * S2 — CalendarContextPill: Shows holiday/weekend name badge.
 * S9 — Also shows auspicious date badge.
 * 
 * Combined into a single context bar for efficiency.
 */

export const EventContextBadge = ({ eventContext }) => {
  if (!eventContext || !eventContext.label) return null;

  return (
    <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-amber-500/10 border border-amber-500/25">
      <span className="text-sm">🏟️</span>
      <span className="text-xs font-bold text-amber-400">{eventContext.label}</span>
      <span className="text-[10px] text-amber-300/60 ml-auto">×{eventContext.multiplier?.toFixed(2)}</span>
    </div>
  );
};

export const CalendarContextPill = ({ calendarContext, auspiciousContext }) => {
  const hasCalendar = calendarContext && calendarContext.name && calendarContext.type !== 'regular';
  const hasAuspicious = auspiciousContext && auspiciousContext.type !== 'none';

  if (!hasCalendar && !hasAuspicious) return null;

  return (
    <div className="flex flex-wrap gap-1.5">
      {hasCalendar && (
        <span className="inline-flex items-center gap-1 px-2 py-1 rounded-md bg-purple-500/10 border border-purple-500/20 text-[10px] font-bold text-purple-400">
          📅 {calendarContext.name}
          <span className="text-purple-300/50">×{calendarContext.multiplier?.toFixed(2)}</span>
        </span>
      )}
      {hasAuspicious && (
        <span className="inline-flex items-center gap-1 px-2 py-1 rounded-md bg-orange-500/10 border border-orange-500/20 text-[10px] font-bold text-orange-400">
          🙏 {auspiciousContext.name}
          <span className="text-orange-300/50">×{auspiciousContext.multiplier?.toFixed(2)}</span>
        </span>
      )}
    </div>
  );
};

export default EventContextBadge;
