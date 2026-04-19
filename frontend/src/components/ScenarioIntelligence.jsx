import React, { useMemo, useState } from 'react';
import axios from 'axios';
import { API_BASE_URL } from '../utils/constants';

/**
 * ScenarioIntelligence — Always-visible panel showing ALL 11 scenario statuses.
 * Upgraded with Interactive Controls (S7 & S10).
 */
const ScenarioIntelligence = ({
  aartiContext = {},
  calendarContext = {},
  eventContext = {},
  auspiciousContext = {},
  processionStatus = {},
  anomalyData = {},
  counterFlowStatus = null,
  clusterData = {},
  tollStatus = [],
  transitStatus = {},
  zoneStatus = {},
  entryFlow = 0,
  exitFlow = 0,
  location = 'Ambaji',
}) => {
  const [loading, setLoading] = useState(null); // 'aarti', 'procession', etc
  const [toast, setToast] = useState(null);
  const [expanded, setExpanded] = useState(null); // scenario id

  const showToast = (msg) => {
    setToast(msg);
    setTimeout(() => setToast(null), 3000);
  };

  const BACKEND_URL = useMemo(() => API_BASE_URL, []);

  // ── S7: Aarti Controls ──────────────────────────────────────────────────
  const aartiActive = aartiContext?.aarti_active;
  const aartiName = aartiContext?.aarti_name;
  const aartiMinutes = aartiContext?.minutes_to_next;
  const aartiMult = aartiContext?.multiplier;

  const toggleAarti = async () => {
    setLoading('aarti');
    try {
      if (aartiActive && aartiContext?.is_manual) {
        await axios.post(`${BACKEND_URL}/api/aarti/stop`, { location });
        showToast('Manual Aarti stopped');
      } else {
        await axios.post(`${BACKEND_URL}/api/aarti/start`, { 
          location, 
          name: "Emergency Aarti",
          multiplier: 1.8 
        });
        showToast('Manual Aarti triggered!');
      }
    } catch (err) {
      console.error(err);
      showToast('Action failed');
    }
    setLoading(null);
  };

  // ── S10: Procession Controls ─────────────────────────────────────────────
  const procActive = processionStatus?.active;
  const procName = processionStatus?.name;
  const procBlock = processionStatus?.block_pct || 0;

  const toggleProcession = async () => {
    setLoading('procession');
    try {
      if (procActive && processionStatus?.is_manual) {
        await axios.post(`${BACKEND_URL}/api/procession/stop`, { location });
        showToast('Procession cleared');
      } else {
        await axios.post(`${BACKEND_URL}/api/procession/start`, {
          location,
          name: "Crowd Surge Yatra",
          block_pct: 65
        });
        showToast('Procession started!');
      }
    } catch (err) {
      console.error(err);
      showToast('Action failed');
    }
    setLoading(null);
  };

  // ── S2/S9: Calendar + Auspicious ───────────────────────────────────────
  const calName = calendarContext?.name || 'Regular day';
  const calType = calendarContext?.type || 'regular';
  const calMult = calendarContext?.multiplier || 1.0;
  const auspType = auspiciousContext?.type || 'none';
  const auspName = auspiciousContext?.name;
  const auspMult = auspiciousContext?.multiplier || 1.0;

  // ── S1: External Event ─────────────────────────────────────────────────
  const eventLabel = eventContext?.label;
  const eventMult = eventContext?.multiplier || 1.0;

  // ── S6: Black Swan ─────────────────────────────────────────────────────
  const anomFlag = anomalyData?.anomaly_flag;
  const anomZ = anomalyData?.z_score || 0;
  const anomSeverity = anomalyData?.anomaly_severity || 'none';
  const aiTriage = anomalyData?.ai_triage;

  // ── S8: Counter-flow ───────────────────────────────────────────────────
  const hasCounterFlow = !!counterFlowStatus;

  // ── S11: Cluster ───────────────────────────────────────────────────────
  const clusterFlag = clusterData?.cluster_flag;
  const clusterSev = clusterData?.cluster_severity || 'none';

  // ── S3/S4: Transit + Toll ──────────────────────────────────────────────
  const transitCorridors = Object.keys(transitStatus || {});
  const tollActive = (tollStatus || []).filter(t => t.tier !== 'NORMAL');
  const zoneRows = Object.values(zoneStatus || {}).filter(z => z?.location === location);
  const maxZoneUtil = zoneRows.length ? Math.max(...zoneRows.map(z => Number(z.utilization_pct || 0))) : 0;
  const zoneCascade = maxZoneUtil >= 80;

  // Helper components
  const StatusDot = ({ active, critical }) => (
    <span className={`inline-block w-2 h-2 rounded-full mr-2 ${
      critical ? 'bg-red-500 animate-pulse' : active ? 'bg-green-500' : 'bg-slate-600'
    }`}></span>
  );

  const ScenarioRow = ({ id, label, active, critical, onTrigger, triggerLabel, loadingTrigger, details, children }) => (
    <div className={`group relative flex items-start gap-2 px-3 py-2 rounded-lg transition-all ${
      critical ? 'bg-red-500/10 border border-red-500/20' 
      : active ? 'bg-emerald-500/5 border border-emerald-500/15' 
      : 'bg-slate-800/30 border border-slate-800/40'
    }`}>
      <StatusDot active={active} critical={critical} />
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <span className="text-[10px] font-black text-slate-500 uppercase tracking-widest">{id}</span>
          <span className="text-xs font-bold text-slate-300">{label}</span>
          {details && (
            <button
              type="button"
              onClick={() => setExpanded(expanded === id ? null : id)}
              className="ml-auto text-[10px] font-black text-slate-500 hover:text-slate-200 uppercase tracking-widest"
            >
              {expanded === id ? 'HIDE' : 'DETAILS'}
            </button>
          )}
        </div>
        <div className="text-[11px] text-slate-400 mt-0.5">{children}</div>
        {details && expanded === id && (
          <pre className="mt-2 text-[10px] leading-relaxed text-slate-400 bg-slate-950/60 border border-slate-800 rounded-lg p-2 overflow-x-auto whitespace-pre-wrap">
            {JSON.stringify(details, null, 2)}
          </pre>
        )}
      </div>
      {onTrigger && (
        <button
          onClick={onTrigger}
          disabled={loadingTrigger}
          className={`opacity-0 group-hover:opacity-100 transition-opacity text-[10px] font-black px-2 py-1 rounded border uppercase tracking-tighter
            ${active ? 'border-amber-500/50 text-amber-500 hover:bg-amber-500/10' : 'border-blue-500/50 text-blue-500 hover:bg-blue-500/10'}
            disabled:opacity-50 cursor-pointer
          `}
        >
          {loadingTrigger ? '...' : triggerLabel}
        </button>
      )}
    </div>
  );

  return (
    <div className="bg-slate-950 border border-slate-800 rounded-xl p-4 shadow-xl relative overflow-hidden">
      {/* Toast Notification */}
      {toast && (
        <div className="absolute top-2 left-1/2 -translate-x-1/2 z-50 bg-blue-600 text-white text-[10px] font-bold px-3 py-1 rounded-full shadow-lg animate-bounce">
          {toast}
        </div>
      )}

      <div className="flex items-center gap-3 mb-4 pb-3 border-b border-slate-800">
        <span className="text-lg">🧠</span>
        <h2 className="text-sm font-black text-white uppercase tracking-wider">Scenario Intelligence</h2>
        <span className="text-[10px] bg-blue-500/15 text-blue-400 px-2 py-0.5 rounded-full font-bold ml-auto">
          11 ACTIVE
        </span>
      </div>

      <div className="space-y-2 max-h-[600px] overflow-y-auto pr-1">

        {/* S7 — Aarti */}
        <ScenarioRow 
          id="S7" 
          label="Aarti / Prayer Timing" 
          active={!!aartiName} 
          critical={aartiActive}
          onTrigger={toggleAarti}
          triggerLabel={aartiActive && aartiContext?.is_manual ? "STOP" : "START"}
          loadingTrigger={loading === 'aarti'}
          details={aartiContext}
        >
          {aartiActive ? (
            <span className="text-red-400 font-bold">🪔 {aartiName} Aarti — ACTIVE · ×{aartiMult?.toFixed(2)}</span>
          ) : aartiName && aartiMinutes != null && aartiMinutes <= 15 ? (
            <span className="text-amber-400">🪔 {aartiName} in {aartiMinutes} min · Pre-surge ×{aartiMult?.toFixed(2)}</span>
          ) : aartiMinutes != null ? (
            <span>Next aarti in ~{aartiMinutes} min</span>
          ) : (
            <span>No upcoming aarti in schedule window</span>
          )}
        </ScenarioRow>

        {/* S10 — Procession */}
        <ScenarioRow 
          id="S10" 
          label="Procession / Yatra" 
          active={procActive} 
          critical={procBlock >= 60}
          onTrigger={toggleProcession}
          triggerLabel={procActive && processionStatus?.is_manual ? "STOP" : "START"}
          loadingTrigger={loading === 'procession'}
          details={processionStatus}
        >
          {procActive ? (
            <span className="text-orange-400 font-bold">🚩 {procName} — corridor {procBlock}% blocked</span>
          ) : (
            <span>No active procession</span>
          )}
        </ScenarioRow>

        {/* S2 — Calendar */}
        <ScenarioRow id="S2" label="Calendar Context" 
          active={calType !== 'regular'} critical={calMult >= 1.5}
          details={calendarContext}>
          <span className={calType !== 'regular' ? 'text-purple-400' : ''}>
            📅 {calName} {calMult > 1 ? `· ×${calMult.toFixed(2)} multiplier` : '· baseline'}
          </span>
        </ScenarioRow>

        {/* S9 — Auspicious */}
        <ScenarioRow id="S9" label="Auspicious Date" 
          active={auspType !== 'none'} critical={auspMult >= 1.7}
          details={auspiciousContext}>
          {auspType !== 'none' ? (
            <span className="text-orange-400">🙏 {auspName} ({auspType}) · ×{auspMult.toFixed(2)}</span>
          ) : (
            <span>No auspicious date today</span>
          )}
        </ScenarioRow>

        {/* S1 — External Event */}
        <ScenarioRow id="S1" label="External Events (IPL/Mela)" 
          active={!!eventLabel} critical={eventMult >= 1.2}
          details={eventContext}>
          {eventLabel ? (
            <span className="text-amber-400">🏟️ {eventLabel} · ×{eventMult.toFixed(2)}</span>
          ) : (
            <span>No active external events near {location || 'corridors'}</span>
          )}
        </ScenarioRow>

        {/* S8 — Counter-Flow */}
        <ScenarioRow id="S8" label="Bidirectional Flow" 
          active={entryFlow > 20 && exitFlow > 15} critical={hasCounterFlow}
          details={{ counter_flow_status: counterFlowStatus, entry_flow: entryFlow, exit_flow: exitFlow }}>
          {hasCounterFlow ? (
            <span className="text-red-400 font-bold">⚠ {counterFlowStatus}</span>
          ) : (
            <span>↑ Entry {entryFlow?.toFixed(0)} · ↓ Exit {exitFlow?.toFixed(0)} pax/min — normal flow</span>
          )}
        </ScenarioRow>

        {/* S6 — Black Swan */}
        <ScenarioRow id="S6" label="Anomaly Detection (Black Swan)" 
          active={anomFlag} critical={anomSeverity === 'critical'}
          details={anomalyData}>
          {anomFlag ? (
            <div>
              <span className={`font-bold ${anomSeverity === 'critical' ? 'text-red-400' : 'text-amber-400'}`}>
                🔮 {anomSeverity.toUpperCase()} · z-score: {anomZ?.toFixed(2)}σ
              </span>
              {aiTriage && (
                <p className="text-[10px] text-slate-400 mt-1 leading-relaxed">{aiTriage}</p>
              )}
            </div>
          ) : (
            <span>z-score: {anomZ?.toFixed(2)}σ — within normal range</span>
          )}
        </ScenarioRow>

        {/* S11 — Cluster */}
        <ScenarioRow id="S11" label="Cluster Formation" 
          active={clusterFlag} critical={clusterSev === 'critical'}
          details={clusterData}>
          {clusterFlag ? (
            <span className={clusterSev === 'critical' ? 'text-red-400 font-bold' : 'text-amber-400'}>
              ⬤ Cluster {clusterSev} — {clusterData?.effective_risk || 'elevated'}
            </span>
          ) : (
            <span>Density distribution: {clusterData?.effective_risk || 'uniform'}</span>
          )}
        </ScenarioRow>

        {/* S3 — In-Transit */}
        <ScenarioRow id="S3" label="In-Transit Crowd" 
          active={transitCorridors.length > 0}
          details={transitStatus}>
          {transitCorridors.length > 0 ? (
            <span className="text-blue-400">🚌 Convoys approaching: {transitCorridors.join(', ')}</span>
          ) : (
            <span>No bus convoys currently tracked</span>
          )}
        </ScenarioRow>

        {/* S4 — Toll Booth */}
        <ScenarioRow id="S4" label="Toll Booth Indicators" 
          active={tollActive.length > 0} critical={tollActive.some(t => t.tier === 'PRE_ARRIVAL_WARNING')}
          details={tollStatus}>
          {tollActive.length > 0 ? (
            <span className="text-amber-400">
              🛣️ {tollActive.length} booth(s) elevated: {
                tollActive.map(t => `${t.booth_id} (${t.surge_ratio?.toFixed(1)}×)`).join(', ')
              }
            </span>
          ) : (
            <span>All toll booths at normal traffic levels</span>
          )}
        </ScenarioRow>

        {/* S5 — Buffer Zone */}
        <ScenarioRow id="S5" label="Buffer Zones" active={zoneRows.length > 0} critical={zoneCascade}
          details={zoneRows}>
          {zoneRows.length > 0 ? (
            <span className={zoneCascade ? 'text-red-400 font-bold' : 'text-amber-300'}>
              Buffer utilization max {maxZoneUtil.toFixed(1)}% {zoneCascade ? '— cascade risk' : '— stable'}
            </span>
          ) : (
            <span>No zone feed for {location}</span>
          )}
        </ScenarioRow>

      </div>
    </div>
  );
};

export default ScenarioIntelligence;
