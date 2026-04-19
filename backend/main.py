"""
Stampede Window Predictor — FastAPI Backend (v2 — Scenario Extensions S1-S11)

Main application with:
  - POST /api/ingest: receive data rows from simulation (enriched pipeline)
  - WS /ws/dashboard: WebSocket push to all connected clients (enriched payload)
  - POST /api/acknowledge: agency acknowledgement
  - GET /api/events: filterable event log
  - POST /api/replay/start: load replay scenario
  - GET /api/replay/frame: get next replay frame
  - GET /api/health: health check
  - POST /api/ingest/transit: transit convoy data (S3)
  - POST /api/ingest/toll: toll booth data (S4)
  - POST /api/ingest/zone: buffer zone data (S5)
  - POST /api/anomaly/context: operator context for AI triage (S6)
  - POST /api/procession/start: start manual procession (S10)
  - POST /api/procession/stop: stop manual procession (S10)
"""

import os
import json
import math
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import joblib
import pandas as pd
import numpy as np
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from database import (
    get_connection, init_db, insert_pressure_reading, insert_alert,
    insert_acknowledgement, insert_event, get_events, get_active_alerts,
    get_alert_acknowledgements,
)
from services.pressure_calculator import compute_pressure_index, compute_combined_zone_pressure
from services.crush_classifier import (
    classify_crush_or_surge, get_history, pressure_history,
    detect_counter_flow, detect_zone_cascade, detect_cluster_formation,
)
from services.alert_manager import (
    should_trigger_alert, get_agency_actions, AGENCY_ACTIONS, ALERT_THRESHOLD,
)

# New scenario services
from services.event_context import get_active_event_context
from services.calendar_context import get_calendar_multiplier
from services.aarti_context import get_aarti_context
from services.lunar_calendar import get_auspicious_context
from services.procession_monitor import (
    get_procession_status, apply_corridor_obstruction,
    start_manual_procession, stop_manual_procession,
)
from services.black_swan_detector import (
    detect_anomaly, get_ai_triage_mock,
    set_operator_context, get_operator_context,
)
from services.toll_analyzer import compute_toll_surge_ratio, get_all_toll_status, get_toll_status_for_corridor
from services.transit_predictor import (
    predict_choke_pressure_from_transit, update_transit_status,
    get_transit_status, get_all_transit_status,
)
from services.sms_notifier import notify_authority_sms_for_alert, send_sms

# Phase M Multi-Entity Services
from services.location_registry import (
    LOCATION_REGISTRY, get_temples, get_active_events,
    get_correlated_events, register_dynamic_event
)
from services.form_factors import get_form_factor, compute_generic_pressure
from services.correlation_engine import map_event_to_correlation

# ─── App Setup ────────────────────────────────────────────────────────────────

app = FastAPI(
    title="Stampede Window Predictor",
    description="Real-time crowd pressure intelligence for pilgrimage corridors",
    version="2.0.0",
)

# CORS — allow frontend dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── In-Memory State ─────────────────────────────────────────────────────────

current_state: Dict[str, dict] = {}      # location → latest computed state
active_alerts: List[dict] = []            # list of active alert objects
connected_clients: List[WebSocket] = []   # WebSocket connections
replay_frames: List[dict] = []            # loaded replay scenario
replay_cursor: int = 0                    # current replay position
flow_history: Dict[str, List[dict]] = {}  # location → last N flow readings
zone_status: Dict[str, dict] = {}        # zone_id → latest zone reading
escalation_task: Optional[asyncio.Task] = None

# ML model (loaded once at startup)
ml_models = None

MODEL_PATH = os.path.join(os.path.dirname(__file__), "..", "dataset", "pkl", "master_crush_window_rf_model.pkl")
FEATURE_COLUMNS = []


# ─── Startup / Shutdown ──────────────────────────────────────────────────────

@app.on_event("startup")
async def startup():
    """Initialize DB and load ML models."""
    global ml_models, escalation_task, FEATURE_COLUMNS

    # Init database
    init_db()

    # Load ML model
    if os.path.exists(MODEL_PATH):
        try:
            ml_models = joblib.load(MODEL_PATH)
            FEATURE_COLUMNS = list(ml_models.feature_names_in_)
            print(f"[ML] Loaded models from {MODEL_PATH}")
            print(f"[ML] Features ({len(FEATURE_COLUMNS)}): {FEATURE_COLUMNS[:5]}...")
        except BaseException as e:
            print(f"[ML] ERROR loading model: {e}")
    else:
        print(f"[ML] WARNING: Model not found at {MODEL_PATH}")
        print(f"[ML] Check path!")

    escalation_task = asyncio.create_task(sms_escalation_loop())


@app.on_event("shutdown")
async def shutdown():
    """Stop background tasks cleanly."""
    global escalation_task
    if escalation_task and not escalation_task.done():
        escalation_task.cancel()
        try:
            await escalation_task
        except asyncio.CancelledError:
            pass


# ─── Pydantic Models ─────────────────────────────────────────────────────────

class IngestPayload(BaseModel):
    timestamp: Optional[str] = None
    location: str
    corridor_width_m: float = 5.0
    entry_flow_rate_pax_per_min: float = 0
    exit_flow_rate_pax_per_min: float = 0
    transport_arrival_burst: float = 0
    vehicle_count: int = 0
    queue_density_pax_per_m2: float = 0
    weather: str = "Clear"
    festival_peak: int = 0
    pressure_index: Optional[float] = None
    risk_level: Optional[str] = None
    predicted_crush_window: Optional[float] = None

    class Config:
        extra = "allow"


class AcknowledgePayload(BaseModel):
    alert_id: int
    agency: str  # 'police', 'temple', 'transport'
    action_taken: Optional[str] = None


class TransitIngestPayload(BaseModel):
    timestamp: Optional[str] = None
    segment_id: str = ""
    bus_id: str = ""
    vehicles_in_transit: int = 0
    avg_occupancy: int = 40
    eta_to_choke_min: float = 14
    target_corridor: str = "Ambaji"
    projected_pressure: Optional[float] = None

    class Config:
        extra = "allow"


class TollIngestPayload(BaseModel):
    timestamp: Optional[str] = None
    booth_id: str
    vehicles_per_min: float = 0
    target_corridor: Optional[str] = None

    class Config:
        extra = "allow"


class ZoneIngestPayload(BaseModel):
    timestamp: Optional[str] = None
    zone_id: str
    zone_type: str = "BUFFER"
    location: str = ""
    utilization_pct: float = 0
    pax_count: int = 0
    capacity: int = 1000

    class Config:
        extra = "allow"


class OperatorContextPayload(BaseModel):
    location: str
    context: str


class ProcessionPayload(BaseModel):
    location: str
    name: str = "Manual procession"
    block_pct: int = 50


class AartiPayload(BaseModel):
    location: str
    name: str = "Surge Aarti"
    multiplier: float = 1.7


class SmsTestPayload(BaseModel):
    phone: str = "7698331412"
    message: str = "TEST: Stampede Predictor SMS gateway check"

class EventRegistrationPayload(BaseModel):
    name: str
    venue_type: str
    lat: float
    lng: float
    radius_km: float = 1.0
    form_factors: List[str] = []

class DynamicEventIngestPayload(BaseModel):
    timestamp: Optional[str] = None
    readings: dict

# ─── Helper: WebSocket Broadcast ─────────────────────────────────────────────

def make_serializable(obj):
    """Convert numpy types and other non-serializable objects to Python types."""
    if isinstance(obj, (np.integer,)):
        return int(obj)
    elif isinstance(obj, (np.floating,)):
        v = float(obj)
        if math.isnan(v) or math.isinf(v):
            return 0.0
        return v
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, dict):
        return {k: make_serializable(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [make_serializable(i) for i in obj]
    elif isinstance(obj, float):
        if math.isnan(obj) or math.isinf(obj):
            return 0.0
        return obj
    return obj


async def broadcast_state():
    """Broadcast current state to all connected WebSocket clients."""
    if not connected_clients:
        return

    # Build combined state payload
    pressure_data = {}
    predictions_data = {}
    classifications_data = {}
    flow_rates_data = {}
    aarti_data = {}
    calendar_data = {}
    event_data = {}
    auspicious_data = {}
    procession_data = {}
    anomaly_data = {}
    counter_flow_data = {}
    cluster_data = {}
    venue_readings_data = {}
    correlation_signals_data = {}

    for loc, state in current_state.items():
        pressure_data[loc] = state.get("pressure_index", 0)
        predictions_data[loc] = {
            "crush_window_min": state.get("crush_window_min", 0),
            "risk_level": state.get("risk_level", "Low"),
        }
        classifications_data[loc] = state.get("classification", "MONITORING")
        flow_rates_data[loc] = {
            "entry": state.get("entry_flow_rate_pax_per_min", 0),
            "exit": state.get("exit_flow_rate_pax_per_min", 0),
        }

        # Scenario context data
        aarti_data[loc] = state.get("aarti_context", {})
        calendar_data[loc] = state.get("calendar_context", {})
        event_data[loc] = state.get("event_context", {})
        auspicious_data[loc] = state.get("auspicious_context", {})
        procession_data[loc] = state.get("procession_status", {})
        anomaly_data[loc] = state.get("anomaly_data", {})
        counter_flow_data[loc] = state.get("counter_flow_status", None)
        cluster_data[loc] = state.get("cluster_data", {})
        venue_readings_data[loc] = state.get("readings") or {}
        correlation_signals_data[loc] = state.get("correlation_signal")

    message = {
        "type": "state_update",
        "data": make_serializable({
            "pressure": pressure_data,
            "predictions": predictions_data,
            "alerts": active_alerts,
            "classifications": classifications_data,
            "flow_rates": flow_rates_data,
            "flow_history": {loc: readings[-20:] for loc, readings in flow_history.items()},
            "locations": list(current_state.keys()),
            "timestamp": datetime.now().isoformat(),
            # Scenario extensions
            "aarti_context": aarti_data,
            "calendar_context": calendar_data,
            "event_context": event_data,
            "auspicious_context": auspicious_data,
            "procession_status": procession_data,
            "anomaly_data": anomaly_data,
            "counter_flow": counter_flow_data,
            "cluster_data": cluster_data,
            "toll_status": get_all_toll_status(),
            "transit_status": get_all_transit_status(),
            "zone_status": dict(zone_status),
            "venue_readings": venue_readings_data,
            "correlation_signals": correlation_signals_data,
        }),
    }

    payload = json.dumps(message)
    disconnected = []

    for client in connected_clients:
        try:
            await client.send_text(payload)
        except Exception:
            disconnected.append(client)

    # Clean up disconnected clients
    for client in disconnected:
        if client in connected_clients:
            connected_clients.remove(client)


async def sms_escalation_loop():
    """
    Background loop: send SMS exactly when due (triggered_at + 60s)
    if no agency acknowledged by then.
    """
    while True:
        try:
            changed = False
            now_ts = datetime.now()
            conn = get_connection()
            try:
                for alert in active_alerts:
                    if alert.get("status") != "active":
                        continue
                    if alert.get("sms_sent"):
                        continue

                    has_any_ack = bool(alert.get("acknowledgements"))
                    if has_any_ack and not alert.get("sms_cancelled"):
                        alert["sms_cancelled"] = True
                        changed = True
                        continue

                    due_at_raw = alert.get("sms_due_at")
                    if not due_at_raw:
                        continue
                    try:
                        due_at = datetime.fromisoformat(due_at_raw)
                    except Exception:
                        continue

                    if now_ts < due_at:
                        continue

                    if has_any_ack:
                        continue

                    sms_result = await asyncio.to_thread(
                        notify_authority_sms_for_alert, alert
                    )
                    alert["sms_sent"] = bool(sms_result.get("sent"))
                    alert["sms_sent_at"] = datetime.now().isoformat() if alert["sms_sent"] else None
                    alert["sms_result"] = sms_result
                    changed = True

                    insert_event(conn, "sms_escalation", alert.get("location", "unknown"), {
                        "alert_id": alert.get("id"),
                        "sent": sms_result.get("sent"),
                        "provider": sms_result.get("provider"),
                        "recipient_count": sms_result.get("recipient_count"),
                        "error": sms_result.get("error"),
                    })
            finally:
                conn.close()

            if changed:
                await broadcast_state()
        except asyncio.CancelledError:
            raise
        except Exception as e:
            print(f"[SMS_ESCALATION_LOOP] error: {e}")

        await asyncio.sleep(1.0)


# ─── ML Prediction Helper ────────────────────────────────────────────────────

def run_ml_prediction(row_dict: dict) -> dict:
    """Run ML models on a data row. Returns predicted risk_level and crush_window_min."""
    if ml_models is None or not FEATURE_COLUMNS:
        return {"risk_level": "Low", "crush_window_min": 15.0}

    # Build feature vector dynamically matching the model's exact signature
    features = {}
    for col in FEATURE_COLUMNS:
        if col.startswith("Event_Type_"):
            target_event = col.replace("Event_Type_", "")
            current_event = str(row_dict.get("Event_Type", "")).strip()
            features[col] = 1.0 if current_event == target_event else 0.0
        elif col.startswith("Location_"):
            target_loc = col.replace("Location_", "")
            current_loc = str(row_dict.get("Location", "")).strip()
            features[col] = 1.0 if current_loc == target_loc else 0.0
        elif col.startswith("Weather_"):
            target_w = col.replace("Weather_", "")
            current_w = str(row_dict.get("Weather", "")).strip().lower()
            features[col] = 1.0 if current_w == target_w else 0.0
        elif col.startswith("Risk Level_"):
            target_r = col.replace("Risk Level_", "")
            current_r = str(row_dict.get("Risk Level", "low")).strip().lower()
            features[col] = 1.0 if current_r == target_r else 0.0
        else:
            try:
                features[col] = float(row_dict.get(col, 0))
            except (ValueError, TypeError):
                features[col] = 0.0

    feature_df = pd.DataFrame([features])

    # Predict directly using the RF estimator
    try:
        crush_window = float(ml_models.predict(feature_df)[0])
    except Exception as e:
        print(f"[ML] Prediction Error: {e}")
        crush_window = 15.0

    risk_level = str(row_dict.get("Risk Level", "Low")).title()

    return {
        "risk_level": risk_level,
        "crush_window_min": round(crush_window, 2),
    }


# ─── Endpoints ────────────────────────────────────────────────────────────────

@app.get("/api/locations")
async def get_locations():
    """Return all active locations (temples + events)."""
    return {
        "temples": [loc.__dict__ for loc in get_temples()],
        "events": [loc.__dict__ for loc in get_active_events()]
    }

@app.post("/api/events/register")
async def register_event(payload: EventRegistrationPayload):
    """Admin endpoint to spin up temporary tracking for a new event."""
    loc = register_dynamic_event(
        name=payload.name,
        venue_type=payload.venue_type,
        lat=payload.lat,
        lng=payload.lng,
        all_temples=[t.name for t in get_temples()],
        radius_km=payload.radius_km,
        form_factors=payload.form_factors,
    )
    return {"status": "ok", "location": loc.__dict__}

@app.post("/api/ingest/event/{event_id}")
async def ingest_dynamic_event(event_id: str, payload: DynamicEventIngestPayload):
    """Ingest readings for a non-temple entity (stadium, rally, etc.)."""
    loc = next((l for l in LOCATION_REGISTRY if l.id == event_id), None)
    if not loc:
        return {"error": "Event not found"}, 404
        
    pressure = compute_generic_pressure(loc.venue_type, payload.readings)
    
    signal = map_event_to_correlation(loc.venue_type, pressure, payload.readings)
    ml_result = run_ml_prediction(payload.readings)
    risk_lvl = ml_result.get("risk_level", "Low")
    
    current_state[event_id] = {
        "location": loc.name,
        "venue_type": loc.venue_type,
        "timestamp": payload.timestamp or datetime.now().isoformat(),
        "pressure_index": round(pressure, 2),
        "readings": payload.readings,
        "correlation_signal": signal,
        "crush_window_min": ml_result.get("crush_window_min", 15.0),
        "risk_level": risk_lvl,
        "classification": "MONITORING" if risk_lvl in ["Low", "Moderate"] else "CRUSH BUILDUP"
    }
    await broadcast_state()
    return {"status": "ok", "pressure": round(pressure, 2), "correlation": signal}

@app.get("/api/health")
async def health():
    """Health check endpoint."""
    return {
        "status": "ok",
        "version": "2.0.0",
        "model_loaded": ml_models is not None,
        "connected_clients": len(connected_clients),
        "active_locations": list(current_state.keys()),
        "active_alerts": len(active_alerts),
        "scenarios_active": ["S1-Events", "S2-Calendar", "S3-Transit", "S4-Toll",
                             "S5-Zones", "S6-BlackSwan", "S7-Aarti", "S8-CounterFlow",
                             "S9-Auspicious", "S10-Procession", "S11-Cluster"],
    }


@app.post("/api/ingest")
async def ingest(payload: IngestPayload):
    """
    Receive one data row from simulation, process it, and broadcast state.

    Enhanced pipeline (v2):
      1. Gather all scenario contexts (S1, S2, S7, S9, S10)
      2. Compute pressure index with all multipliers + penalties
      3. Run ML prediction
      4. Classify crush vs surge + counter-flow (S8) + cluster (S11)
      5. Detect anomaly (S6)
      6. Check alert trigger
      7. Store in DB
      8. Broadcast enriched state to all WebSocket clients
    """
    row = payload.model_dump()
    location = row["location"]
    timestamp_str = row.get("timestamp") or datetime.now().isoformat()

    try:
        now = datetime.fromisoformat(str(timestamp_str))
    except (ValueError, TypeError):
        now = datetime.now()

    date_str = now.strftime("%Y-%m-%d")

    # ── 1. Gather all scenario contexts ────────────────────────────────────

    # S1: External event context
    event_ctx = get_active_event_context(location, now)

    # S2: Calendar/holiday context
    calendar_ctx = get_calendar_multiplier(date_str)

    # S7: Aarti timing context
    aarti_ctx = get_aarti_context(location, now)

    # S9: Auspicious date context
    auspicious_ctx = get_auspicious_context(location, date_str)

    # S10: Procession status
    procession_ctx = get_procession_status(location, now)

    # Enrich row with scenario signals for ML prediction
    row["aarti_active"] = 1 if aarti_ctx["aarti_active"] else 0
    row["minutes_to_aarti"] = aarti_ctx.get("minutes_to_next", 0) or 0
    row["calendar_mult"] = calendar_ctx["multiplier"]
    row["event_mult"] = event_ctx["multiplier"]
    row["flow_conflict_penalty"] = float(row.get("flow_conflict_penalty", 0))
    row["density_variance"] = float(row.get("density_variance", 0))
    row["cluster_flag"] = 0 # Will be updated below
    row["anomaly_flag"] = 0 # Will be updated below

    # S5: Buffer zone pressure (from latest zone readings)
    buffer_penalty = 0
    for zid, zdata in zone_status.items():
        if zdata.get("location") == location and zdata.get("zone_type") == "BUFFER":
            buffer_penalty = max(buffer_penalty, compute_combined_zone_pressure(0, zdata.get("utilization_pct", 0)))

    # Phase M: Regional correlated events multiplier
    regional_events = get_correlated_events(location)
    regional_event_mult = 1.0
    for rev in regional_events:
        st = current_state.get(rev.id)
        if st and "correlation_signal" in st:
            regional_event_mult *= st["correlation_signal"]["compound_mult"]

    effective_event_mult = event_ctx["multiplier"] * regional_event_mult

    # Build context dict for pressure calculator
    pressure_context = {
        "event_mult": effective_event_mult,
        "calendar_mult": calendar_ctx["multiplier"],
        "aarti_mult": aarti_ctx["multiplier"],
        "auspicious_mult": auspicious_ctx["multiplier"],
        "buffer_zone_penalty": buffer_penalty,
        "procession_block_pct": procession_ctx["block_pct"] if procession_ctx["active"] else 0,
    }

    # If there is already an active alert for this location, we may need to:
    # - freeze dashboard state for 60s (so operators see stable critical snapshot)
    # - send SMS escalation after 60s if nobody acknowledged
    existing_active_alert = next(
        (a for a in active_alerts if a.get("location") == location and a.get("status") == "active"),
        None,
    )

    # ── 2. Compute pressure index with enriched context ────────────────────
    pressure = compute_pressure_index(row, context=pressure_context)

    # ── 3. ML predictions ──────────────────────────────────────────────────
    ml_result = run_ml_prediction(row)

    # ── 4. Classifications ─────────────────────────────────────────────────
    classification = classify_crush_or_surge(location, pressure)

    # S8: Counter-flow detection
    entry_flow = float(row.get("entry_flow_rate_pax_per_min", 0))
    exit_flow = float(row.get("exit_flow_rate_pax_per_min", 0))
    corridor_width = float(row.get("corridor_width_m", 4.2))
    counter_flow_status = detect_counter_flow(entry_flow, exit_flow, corridor_width)

    density_variance = float(row.get("density_variance", 0))
    cluster_zone_density = float(row.get("cluster_zone_density", 0))
    avg_density = float(row.get("queue_density_pax_per_m2", 0))
    cluster_result = detect_cluster_formation(avg_density, density_variance, cluster_zone_density)
    row["cluster_flag"] = 1 if cluster_result.get("cluster_severity") != "low" else 0

    # S5: Zone cascade detection
    zone_cascade_status = None
    max_buffer_util = 0
    for zid, zdata in zone_status.items():
        if zdata.get("location") == location and zdata.get("zone_type") == "BUFFER":
            max_buffer_util = max(max_buffer_util, zdata.get("utilization_pct", 0))
    if max_buffer_util > 0:
        zone_cascade_status = detect_zone_cascade(location, max_buffer_util, pressure)

    # ── 5. Anomaly detection (S6) ──────────────────────────────────────────
    anomaly_result = detect_anomaly(location, pressure)
    row["anomaly_flag"] = 1 if anomaly_result["anomaly_flag"] else 0

    # Re-run ML prediction with final flags if they were updated
    ml_result = run_ml_prediction(row)

    # Generate triage if anomaly detected
    ai_triage = None
    if anomaly_result["anomaly_flag"]:
        operator_ctx = get_operator_context(location)
        ai_triage = get_ai_triage_mock(
            location, pressure, classification, anomaly_result, operator_ctx
        )

    # ── 6. Alert trigger check ─────────────────────────────────────────────
    should_alert = (
        pressure >= ALERT_THRESHOLD
        and classification == "GENUINE CRUSH BUILDUP"
    )

    # Also trigger for critical anomalies and localized hazards
    if anomaly_result.get("anomaly_severity") == "critical" and pressure > 60:
        should_alert = True
    if counter_flow_status and "CRITICAL" in counter_flow_status:
        should_alert = True
    if cluster_result.get("cluster_severity") == "critical":
        should_alert = True

    # Freeze dashboard state if alert is active and within freeze window.
    # This ensures pressure/countdown/classification do not immediately fall back
    # to normal readings while operators are expected to acknowledge.
    now_ts = datetime.now()
    freeze_active = False
    if existing_active_alert and existing_active_alert.get("freeze_until"):
        try:
            freeze_until = datetime.fromisoformat(existing_active_alert["freeze_until"])
            freeze_active = now_ts < freeze_until
        except Exception:
            freeze_active = False

    if freeze_active and existing_active_alert.get("snapshot"):
        snap = existing_active_alert["snapshot"]
        pressure = float(snap.get("pressure_index", pressure))
        classification = snap.get("classification", classification)
        ml_result = {
            "risk_level": snap.get("risk_level", ml_result.get("risk_level", "Low")),
            "crush_window_min": snap.get("crush_window_min", ml_result.get("crush_window_min", 15.0)),
        }

    # ── 7. Update in-memory state ──────────────────────────────────────────
    current_state[location] = {
        "location": location,
        "timestamp": timestamp_str,
        "pressure_index": round(pressure, 2),
        "risk_level": ml_result["risk_level"],
        "crush_window_min": ml_result["crush_window_min"],
        "classification": classification,
        "entry_flow_rate_pax_per_min": entry_flow,
        "exit_flow_rate_pax_per_min": exit_flow,
        "transport_arrival_burst": row.get("transport_arrival_burst", 0),
        "queue_density_pax_per_m2": avg_density,
        "corridor_width_m": corridor_width,
        "weather": row.get("weather", "Clear"),
        "festival_peak": row.get("festival_peak", 0),
        "vehicle_count": row.get("vehicle_count", 0),
        # Scenario contexts
        "aarti_context": aarti_ctx,
        "calendar_context": calendar_ctx,
        "event_context": {
            "label": event_ctx["label"],
            "multiplier": event_ctx["multiplier"],
            "event_id": event_ctx.get("event_id"),
        },
        "auspicious_context": auspicious_ctx,
        "procession_status": procession_ctx,
        "anomaly_data": {
            **anomaly_result,
            "ai_triage": ai_triage,
        },
        "counter_flow_status": counter_flow_status,
        "cluster_data": cluster_result,
        "zone_cascade": zone_cascade_status,
    }

    # Track flow history for charts
    if location not in flow_history:
        flow_history[location] = []
    flow_history[location].append({
        "timestamp": timestamp_str,
        "entry": entry_flow,
        "exit": exit_flow,
        "pressure": round(pressure, 2),
    })
    # Keep last 50 readings
    if len(flow_history[location]) > 50:
        flow_history[location] = flow_history[location][-50:]

    # ── 8. Write to DB ─────────────────────────────────────────────────────
    alert_created = None
    sms_escalation = None
    conn = get_connection()
    try:
        insert_pressure_reading(conn, {
            "timestamp": timestamp_str,
            "location": location,
            "pressure_index": round(pressure, 2),
            "entry_flow_rate_pax_per_min": entry_flow,
            "exit_flow_rate_pax_per_min": exit_flow,
            "transport_arrival_burst": row.get("transport_arrival_burst", 0),
            "queue_density_pax_per_m2": avg_density,
            "risk_level": ml_result["risk_level"],
            "crush_window_min": ml_result["crush_window_min"],
        })

        # Handle alert create
        if should_alert:
            existing = [a for a in active_alerts if a["location"] == location and a["status"] == "active"]
            if not existing:
                # Determine scenario type for agency actions
                scenario_type = None
                if anomaly_result.get("anomaly_severity") == "critical":
                    scenario_type = "black_swan"
                elif counter_flow_status:
                    scenario_type = "counter_flow"
                elif procession_ctx["active"]:
                    scenario_type = "procession_active"

                alert_id = insert_alert(conn, {
                    "location": location,
                    "pressure_index": round(pressure, 2),
                    "classification": classification,
                    "crush_window_min": ml_result["crush_window_min"],
                })
                alert_obj = {
                    "id": alert_id,
                    "location": location,
                    "pressure_index": round(pressure, 2),
                    "classification": classification,
                    "crush_window_min": ml_result["crush_window_min"],
                    "triggered_at": datetime.now().isoformat(),
                    "status": "active",
                    "agency_actions": get_agency_actions(location, scenario=scenario_type),
                    "acknowledgements": {},
                    "scenario": scenario_type or "crush_alert",
                    "anomaly_data": anomaly_result if anomaly_result["anomaly_flag"] else None,
                    # Freeze + escalation mechanics
                    "freeze_until": (now_ts + timedelta(seconds=15)).isoformat(),
                    "sms_due_at": (now_ts + timedelta(seconds=15)).isoformat(),
                    "sms_sent": False,
                    "sms_sent_at": None,
                    "sms_cancelled": False,
                    "snapshot": {
                        "pressure_index": round(pressure, 2),
                        "risk_level": ml_result["risk_level"],
                        "crush_window_min": ml_result["crush_window_min"],
                        "classification": classification,
                        "counter_flow_status": counter_flow_status,
                        "cluster_data": cluster_result,
                    },
                }
                active_alerts.append(alert_obj)
                alert_created = alert_obj

                insert_event(conn, "alert_triggered", location, {
                    "pressure_index": round(pressure, 2),
                    "classification": classification,
                    "crush_window_min": ml_result["crush_window_min"],
                    "alert_id": alert_id,
                    "scenario": scenario_type,
                })

                # SMS is NOT sent immediately. It is scheduled for +60s only if nobody acknowledges.
                sms_escalation = {
                    "enabled": True,
                    "scheduled": True,
                    "due_at": alert_obj["sms_due_at"],
                    "sent": False,
                    "provider": "android_sms_gateway",
                    "error": None,
                }

    finally:
        conn.close()

    # ── 9. Broadcast to all WebSocket clients ──────────────────────────────
    await broadcast_state()

    return {
        "status": "ok",
        "location": location,
        "pressure_index": round(pressure, 2),
        "risk_level": ml_result["risk_level"],
        "crush_window_min": ml_result["crush_window_min"],
        "classification": classification,
        "alert_triggered": alert_created is not None,
        "sms_escalation": sms_escalation,
        "context": {
            "aarti": aarti_ctx.get("aarti_name"),
            "calendar": calendar_ctx.get("name"),
            "event": event_ctx.get("label"),
            "auspicious": auspicious_ctx.get("name"),
            "procession": procession_ctx.get("name") if procession_ctx["active"] else None,
            "anomaly": anomaly_result["anomaly_severity"] if anomaly_result["anomaly_flag"] else None,
            "counter_flow": counter_flow_status,
        },
    }


@app.websocket("/ws/dashboard")
async def websocket_dashboard(websocket: WebSocket):
    """WebSocket endpoint for real-time dashboard updates."""
    await websocket.accept()
    connected_clients.append(websocket)
    print(f"[WS] Client connected. Total: {len(connected_clients)}")

    try:
        # Send current state immediately on connect
        await broadcast_state()

        # Keep connection alive — listen for pings/messages
        while True:
            data = await websocket.receive_text()
            # Client can send ping to keep alive
            if data == "ping":
                await websocket.send_text(json.dumps({"type": "pong"}))
    except WebSocketDisconnect:
        pass
    except Exception as e:
        print(f"[WS] Error: {e}")
    finally:
        if websocket in connected_clients:
            connected_clients.remove(websocket)
        print(f"[WS] Client disconnected. Total: {len(connected_clients)}")


@app.post("/api/acknowledge")
async def acknowledge(payload: AcknowledgePayload):
    """Record an agency acknowledgement for an alert."""
    alert_id = payload.alert_id
    agency = payload.agency.lower()
    action_taken = payload.action_taken or AGENCY_ACTIONS.get(agency, "Action taken")

    # Find the alert
    alert = None
    for a in active_alerts:
        if a["id"] == alert_id:
            alert = a
            break

    if not alert:
        return {"status": "error", "message": f"Alert {alert_id} not found"}

    # Check if already acknowledged by this agency
    if agency in alert.get("acknowledgements", {}):
        return {"status": "error", "message": f"{agency} already acknowledged alert {alert_id}"}

    # Calculate response time
    triggered_at = datetime.fromisoformat(alert["triggered_at"])
    response_time_sec = int((datetime.now() - triggered_at).total_seconds())

    # Record acknowledgement
    alert.setdefault("acknowledgements", {})[agency] = {
        "acknowledged_at": datetime.now().isoformat(),
        "response_time_sec": response_time_sec,
        "action_taken": action_taken,
    }

    # Requirement: if acknowledged within 1 minute, do not send SMS escalation.
    if not alert.get("sms_sent"):
        alert["sms_cancelled"] = True

    # Update agency action card
    if "agency_actions" in alert:
        for action_card in alert["agency_actions"]:
            if action_card["agency"] == agency:
                action_card["acknowledged"] = True
                action_card["response_time_sec"] = response_time_sec

    # Check if all agencies have acknowledged
    all_agencies = set(AGENCY_ACTIONS.keys())
    acked_agencies = set(alert.get("acknowledgements", {}).keys())
    if all_agencies.issubset(acked_agencies):
        alert["status"] = "acknowledged"

    # Write to DB
    conn = get_connection()
    try:
        insert_acknowledgement(conn, {
            "alert_id": alert_id,
            "agency": agency,
            "response_time_sec": response_time_sec,
            "action_taken": action_taken,
        })
        insert_event(conn, "acknowledgement", alert["location"], {
            "alert_id": alert_id,
            "agency": agency,
            "response_time_sec": response_time_sec,
        })
    finally:
        conn.close()

    # Broadcast updated state
    await broadcast_state()

    return {
        "status": "ok",
        "alert_id": alert_id,
        "agency": agency,
        "response_time_sec": response_time_sec,
    }


@app.get("/api/events")
async def events(
    location: Optional[str] = Query(None),
    risk_level: Optional[str] = Query(None),
    limit: int = Query(200, ge=1, le=1000),
):
    """Get event log with optional filters."""
    conn = get_connection()
    try:
        result = get_events(conn, location=location, risk_level=risk_level, limit=limit)
        return {"status": "ok", "events": result, "total": len(result)}
    finally:
        conn.close()


# ─── Replay Endpoints ────────────────────────────────────────────────────────

@app.post("/api/replay/start")
async def replay_start():
    """Load replay scenario CSV into memory."""
    global replay_frames, replay_cursor

    replay_path = os.path.join(os.path.dirname(__file__), "..", "data", "replay_scenario.csv")

    if not os.path.exists(replay_path):
        return {"status": "error", "message": "replay_scenario.csv not found"}

    df = pd.read_csv(replay_path)
    replay_frames = df.to_dict(orient="records")
    replay_cursor = 0

    return {
        "status": "ok",
        "total_frames": len(replay_frames),
        "message": f"Loaded {len(replay_frames)} replay frames",
    }


@app.get("/api/replay/frame")
async def replay_frame():
    """Return next frame from loaded replay scenario."""
    global replay_cursor

    if not replay_frames:
        return {"status": "error", "message": "No replay loaded. Call POST /api/replay/start first"}

    if replay_cursor >= len(replay_frames):
        return {
            "status": "done",
            "message": "Replay complete",
            "total_frames": len(replay_frames),
        }

    frame = replay_frames[replay_cursor]
    frame_index = replay_cursor
    replay_cursor += 1

    return {
        "status": "ok",
        "frame_index": frame_index,
        "total_frames": len(replay_frames),
        "data": make_serializable(frame),
    }


@app.post("/api/replay/reset")
async def replay_reset():
    """Reset replay cursor to beginning."""
    global replay_cursor
    replay_cursor = 0
    return {"status": "ok", "message": "Replay cursor reset to 0"}


@app.get("/api/alerts")
async def get_alerts():
    """Get all active alerts with acknowledgement status."""
    return {
        "status": "ok",
        "alerts": make_serializable(active_alerts),
        "total": len(active_alerts),
    }


# ─── S3: Transit Ingest ──────────────────────────────────────────────────────

@app.post("/api/ingest/transit")
async def ingest_transit(payload: TransitIngestPayload):
    """S3 — Ingest in-transit bus convoy data and compute projected pressure."""
    row = payload.model_dump()

    # Compute projected choke pressure
    prediction = predict_choke_pressure_from_transit(
        vehicles_in_transit=row["vehicles_in_transit"],
        avg_occupancy=row["avg_occupancy"],
        eta_to_choke_min=row["eta_to_choke_min"],
    )

    # Store latest status
    update_transit_status(row["target_corridor"], {
        **prediction,
        "timestamp": row.get("timestamp") or datetime.now().isoformat(),
        "segment_id": row.get("segment_id"),
    })

    # Broadcast updated state
    await broadcast_state()

    return {"status": "ok", **prediction}


# ─── S4: Toll Ingest ─────────────────────────────────────────────────────────

@app.post("/api/ingest/toll")
async def ingest_toll(payload: TollIngestPayload):
    """S4 — Ingest toll booth reading and compute surge ratio."""
    row = payload.model_dump()
    result = compute_toll_surge_ratio(row["booth_id"], row["vehicles_per_min"])

    # Broadcast updated state
    await broadcast_state()

    return {"status": "ok", **result}


# ─── S5: Zone Ingest ─────────────────────────────────────────────────────────

@app.post("/api/ingest/zone")
async def ingest_zone(payload: ZoneIngestPayload):
    """S5 — Ingest buffer zone reading."""
    row = payload.model_dump()

    zone_status[row["zone_id"]] = {
        "zone_id": row["zone_id"],
        "zone_type": row["zone_type"],
        "location": row["location"],
        "utilization_pct": row["utilization_pct"],
        "pax_count": row["pax_count"],
        "capacity": row["capacity"],
        "timestamp": row.get("timestamp") or datetime.now().isoformat(),
    }

    # Broadcast updated state
    await broadcast_state()

    return {"status": "ok", "zone_id": row["zone_id"], "utilization_pct": row["utilization_pct"]}


# ─── S6: Operator Context ────────────────────────────────────────────────────

@app.post("/api/anomaly/context")
async def anomaly_context(payload: OperatorContextPayload):
    """S6 — Set operator context for AI triage enrichment."""
    set_operator_context(payload.location, payload.context)
    return {"status": "ok", "location": payload.location, "context": payload.context}


# ─── S10: Procession Control ─────────────────────────────────────────────────

@app.post("/api/procession/start")
async def procession_start(payload: ProcessionPayload):
    """S10 — Operator: start a manual procession at a location."""
    start_manual_procession(payload.location, payload.name, payload.block_pct)
    await broadcast_state()
    return {"status": "ok", "location": payload.location, "name": payload.name, "block_pct": payload.block_pct}


@app.post("/api/procession/stop")
async def procession_stop(payload: ProcessionPayload):
    """S10 — Operator: stop a manual procession at a location."""
    stop_manual_procession(payload.location)
    await broadcast_state()
    return {"status": "ok", "location": payload.location, "stopped": True}


# ─── S7: Aarti Control ───────────────────────────────────────────────────────

@app.post("/api/aarti/start")
async def aarti_start(payload: AartiPayload):
    """S7 — Operator: start a manual aarti surge at a location."""
    from services.aarti_context import start_manual_aarti
    start_manual_aarti(payload.location, payload.name, payload.multiplier)
    await broadcast_state()
    return {"status": "ok", "location": payload.location, "name": payload.name, "multiplier": payload.multiplier}


@app.post("/api/aarti/stop")
async def aarti_stop(payload: AartiPayload):
    """S7 — Operator: stop manual aarti surge."""
    from services.aarti_context import stop_manual_aarti
    stop_manual_aarti(payload.location)
    await broadcast_state()
    return {"status": "ok", "location": payload.location, "stopped": True}


@app.post("/api/sms/test")
async def sms_test(payload: SmsTestPayload):
    """Send a test SMS immediately (no delay)."""
    result = await asyncio.to_thread(send_sms, payload.phone, payload.message)
    return {"status": "ok" if result.get("success") else "error", "result": result}
