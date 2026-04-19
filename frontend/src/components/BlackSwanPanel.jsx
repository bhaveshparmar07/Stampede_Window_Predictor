import React, { useState } from 'react';

/**
 * S6 — BlackSwanPanel: Anomaly detection display with AI triage and operator context input.
 * Shows z-score severity indicator + AI-generated triage text + operator note field.
 */

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

const BlackSwanPanel = ({ anomalyData, location }) => {
  const [operatorNote, setOperatorNote] = useState('');
  const [sending, setSending] = useState(false);

  if (!anomalyData || !anomalyData.anomaly_flag) return null;

  const { z_score, anomaly_severity, ai_triage } = anomalyData;

  const severityConfig = {
    critical: { color: '#ef4444', bg: 'bg-red-500/10', border: 'border-red-500/30', label: 'CRITICAL ANOMALY' },
    moderate: { color: '#eab308', bg: 'bg-amber-500/10', border: 'border-amber-500/30', label: 'MODERATE ANOMALY' },
    none:     { color: '#64748b', bg: 'bg-slate-800', border: 'border-slate-700', label: 'MONITORING' },
  };

  const cfg = severityConfig[anomaly_severity] || severityConfig.none;

  const handleSubmitContext = async () => {
    if (!operatorNote.trim()) return;
    setSending(true);
    try {
      await fetch(`${API_BASE}/api/anomaly/context`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ location, context: operatorNote }),
      });
      setOperatorNote('');
    } catch (err) {
      console.error('Failed to send operator context:', err);
    }
    setSending(false);
  };

  return (
    <div className={`${cfg.bg} border ${cfg.border} rounded-xl p-4 space-y-3`}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="text-lg">🔮</span>
          <span className="text-xs font-black uppercase tracking-wider" style={{ color: cfg.color }}>
            {cfg.label}
          </span>
        </div>
        <div className="flex items-center gap-1.5">
          <span className="text-[10px] text-slate-500">Z-Score</span>
          <span className="text-sm font-black tabular-nums px-2 py-0.5 rounded-md"
                style={{ backgroundColor: `${cfg.color}20`, color: cfg.color }}>
            {z_score?.toFixed(2)}σ
          </span>
        </div>
      </div>

      {/* AI Triage */}
      {ai_triage && (
        <div className="bg-slate-900/50 rounded-lg p-3 border border-slate-700/30">
          <div className="text-[10px] font-bold text-slate-500 uppercase mb-1.5">AI Triage Analysis</div>
          <p className="text-xs text-slate-300 leading-relaxed">{ai_triage}</p>
        </div>
      )}

      {/* Operator Context Input */}
      <div className="flex gap-2">
        <input
          type="text"
          className="flex-1 bg-slate-900 border border-slate-700 rounded-md px-3 py-1.5 text-xs text-white placeholder-slate-600 focus:outline-none focus:border-slate-500"
          placeholder="Operator note: e.g. 'flash flood on NH947'..."
          value={operatorNote}
          onChange={(e) => setOperatorNote(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleSubmitContext()}
        />
        <button
          onClick={handleSubmitContext}
          disabled={sending || !operatorNote.trim()}
          className="px-3 py-1.5 bg-slate-700 hover:bg-slate-600 text-xs font-bold text-white rounded-md disabled:opacity-40 transition-colors"
        >
          {sending ? '...' : 'Send'}
        </button>
      </div>
    </div>
  );
};

export default BlackSwanPanel;
