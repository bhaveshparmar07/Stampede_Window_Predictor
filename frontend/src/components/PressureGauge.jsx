import React from 'react';
import { PRESSURE_THRESHOLDS } from '../utils/constants';

const getThreshold = (value) => {
  if (value < PRESSURE_THRESHOLDS.watch.min) return PRESSURE_THRESHOLDS.safe;
  if (value < PRESSURE_THRESHOLDS.critical.min) return PRESSURE_THRESHOLDS.watch;
  return PRESSURE_THRESHOLDS.critical;
};

const PressureGauge = ({ value = 0, size = "md" }) => {
  const threshold = getThreshold(value);
  const percentage = Math.min(Math.max(value, 0), 100);
  
  // SVG arc calculation
  const radius = 40;
  const circumference = 2 * Math.PI * radius;
  // Use 75% of the circle for the gauge (270 degrees)
  const arcLength = circumference * 0.75;
  const strokeDashoffset = arcLength - (arcLength * percentage) / 100;
  
  const sizeClasses = {
    sm: "w-24 h-24",
    md: "w-32 h-32",
    lg: "w-48 h-48",
  };
  
  const textClasses = {
    sm: "text-2xl",
    md: "text-4xl",
    lg: "text-6xl",
  };

  return (
    <div className="flex flex-col items-center">
      <div className={`relative ${sizeClasses[size]}`}>
        {/* Background track */}
        <svg className="w-full h-full transform -rotate-135" viewBox="0 0 100 100">
          <circle
            cx="50"
            cy="50"
            r={radius}
            fill="transparent"
            stroke="#1e293b"
            strokeWidth="10"
            strokeDasharray={`${arcLength} ${circumference}`}
            strokeLinecap="round"
          />
          {/* Active value track */}
          <circle
            cx="50"
            cy="50"
            r={radius}
            fill="transparent"
            stroke={threshold.color}
            strokeWidth="10"
            strokeDasharray={`${arcLength} ${circumference}`}
            strokeDashoffset={strokeDashoffset}
            strokeLinecap="round"
            className="transition-all duration-500 ease-out"
          />
        </svg>
        
        {/* Value text */}
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className={`font-bold tabular-nums ${textClasses[size]}`} style={{ color: threshold.color }}>
            {Math.round(value)}
          </span>
          <span className="text-xs text-slate-500 font-medium uppercase tracking-wider mt-1">
            Index
          </span>
        </div>
      </div>
      {size !== 'sm' && (
        <div 
          className="mt-2 px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider"
          style={{ backgroundColor: `${threshold.color}20`, color: threshold.color }}
        >
          {threshold.label}
        </div>
      )}
    </div>
  );
};

export default PressureGauge;
