import React from 'react';
import { Clock } from 'lucide-react';

const CrushCountdown = ({ minutes = 15, isSafe = false }) => {
  // Convert minutes (float) to MM:SS
  const totalSeconds = Math.max(0, Math.floor(minutes * 60));
  const m = Math.floor(totalSeconds / 60);
  const s = totalSeconds % 60;
  
  const isCritical = !isSafe && minutes <= 5;
  const isWarning = !isSafe && minutes <= 10 && minutes > 5;
  
  let colorClass = "text-green-500";
  let bgClass = "bg-green-500/10 border-green-500/30";
  
  if (isCritical) {
    colorClass = "text-red-500 animate-pulse-fast";
    bgClass = "bg-red-500/10 border-red-500/20";
  } else if (isWarning) {
    colorClass = "text-yellow-500";
    bgClass = "bg-yellow-500/10 border-yellow-500/30";
  }

  return (
    <div className={`flex flex-col items-center justify-center p-6 rounded-xl border ${bgClass} transition-colors duration-300`}>
      <div className="flex items-center space-x-2 mb-2">
        <Clock className={colorClass} size={20} />
        <span className="text-sm font-semibold tracking-wide text-slate-300 uppercase">
          Est. Crush Window
        </span>
      </div>
      
      <div className={`text-5xl font-mono font-bold tracking-tight ${colorClass}`}>
        {isSafe ? "--:--" : `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`}
      </div>
      
      <div className="mt-3 text-xs text-slate-500 text-center max-w-[200px]">
        {isSafe ? "Pressure levels remain safely below thresholds" : "Time until pressure exceeds critical threshold"}
      </div>
    </div>
  );
};

export default CrushCountdown;

