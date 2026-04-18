import React from 'react';
import { AlertCircle, Activity, CheckCircle2 } from 'lucide-react';

const SurgeClassifier = ({ classification = "MONITORING" }) => {
  let config = {
    icon: <CheckCircle2 size={18} />,
    color: "text-green-400",
    bg: "bg-green-400/10 border-green-400/20",
    label: "Monitoring",
    desc: "Pressure is stable or low."
  };

  if (classification === "GENUINE CRUSH BUILDUP") {
    config = {
      icon: <AlertCircle size={18} />,
      color: "text-red-500",
      bg: "bg-red-500/10 border-red-500/30",
      label: classification,
      desc: "Consistent pressure rise detected. Prepare to act."
    };
  } else if (classification === "MOMENTARY SURGE — SELF-RESOLVING") {
    config = {
      icon: <Activity size={18} />,
      color: "text-yellow-400",
      bg: "bg-yellow-400/10 border-yellow-400/30",
      label: "MOMENTARY SURGE",
      desc: "Spike detected but already dropping. Monitor closely."
    };
  }

  return (
    <div className={`flex items-start space-x-4 p-4 rounded-xl border ${config.bg}`}>
      <div className={`mt-0.5 ${config.color}`}>
        {config.icon}
      </div>
      <div>
        <h3 className={`font-bold tracking-wide ${config.color}`}>
          {config.label}
        </h3>
        <p className="text-sm text-slate-300 mt-1">
          {config.desc}
        </p>
      </div>
    </div>
  );
};

export default SurgeClassifier;
