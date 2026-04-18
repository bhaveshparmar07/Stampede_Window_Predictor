"""
Stampede Window Predictor — FastAPI Backend

Main application with:
  - POST /api/ingest: receive data rows from simulation
  - WS /ws/dashboard: WebSocket push to all connected clients
  - POST /api/acknowledge: agency acknowledgement
  - GET /api/events: filterable event log
  - POST /api/replay/start: load replay scenario
  - GET /api/replay/frame: get next replay frame
  - GET /api/health: health check
"""

import os
import json
import math
from datetime import datetime
from typing import Dict, List, Optional

import joblib
import pandas as pd
import numpy as np
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from database import get_connection, init_db, insert_pressure_reading, insert_alert, insert_acknowledgement, insert_event, get_events, get_active_alerts, get_alert_acknowledgements
from services.pressure_calculator import compute_pressure_index
from services.crush_classifier import classify_crush_or_surge, get_history, pressure_history
from services.alert_manager import should_trigger_alert, get_agency_actions, AGENCY_ACTIONS, ALERT_THRESHOLD

# ─── App Setup ────────────────────────────────────────────────────────────────

app = FastAPI(
    title="Stampede Window Predictor",
    description="Real-time crowd pressure intelligence for pilgrimage corridors",
    version="1.0.0",
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

# ML model (loaded once at startup)
ml_models = None

MODEL_PATH = os.path.join(os.path.dirname(__file__), "models", "saved_model.pkl")
FEATURE_COLUMNS = [
    "entry_flow_rate_pax_per_min",
    "exit_flow_rate_pax_per_min",
    "transport_arrival_burst",
    "vehicle_count",
    "queue_density_pax_per_m2",
    "corridor_width_m",
    "festival_peak",
    "weather_encoded",
]


# ─── Startup / Shutdown ──────────────────────────────────────────────────────

@app.on_event("startup")
async def startup():
    """Initialize DB and load ML models."""
    global ml_models

    # Init database
    init_db()

    # Load ML model (T-015b)
    if os.path.exists(MODEL_PATH):
        ml_models = joblib.load(MODEL_PATH)
        print(f"[ML] Loaded models from {MODEL_PATH}")
        print(f"[ML] Features: {ml_models['feature_columns']}")
    else:
        print(f"[ML] WARNING: Model not found at {MODEL_PATH}")
        print(f"[ML] Run 'python models/train_model.py' first")


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


# ─── ML Prediction Helper ────────────────────────────────────────────────────

def run_ml_prediction(row_dict: dict) -> dict:
    """Run ML models on a data row. Returns predicted risk_level and crush_window_min."""
    if ml_models is None:
        return {"risk_level": "Low", "crush_window_min": 15.0}

    # Encode weather
    weather = row_dict.get("weather", "Clear")
    try:
        weather_encoded = int(ml_models["weather_encoder"].transform([weather])[0])
    except ValueError:
        weather_encoded = 0  # unknown weather → default encoding

    # Build feature vector
    features = {}
    for col in FEATURE_COLUMNS:
        if col == "weather_encoded":
            features[col] = weather_encoded
        else:
            features[col] = float(row_dict.get(col, 0))

    feature_df = pd.DataFrame([features])

    # Predict
    risk_level = ml_models["classifier"].predict(feature_df)[0]
    crush_window = float(ml_models["regressor"].predict(feature_df)[0])

    return {
        "risk_level": str(risk_level),
        "crush_window_min": round(crush_window, 2),
    }


# ─── Endpoints ────────────────────────────────────────────────────────────────

@app.get("/api/health")
async def health():
    """Health check endpoint."""
    return {
        "status": "ok",
        "model_loaded": ml_models is not None,
        "connected_clients": len(connected_clients),
        "active_locations": list(current_state.keys()),
        "active_alerts": len(active_alerts),
    }


@app.post("/api/ingest")
async def ingest(payload: IngestPayload):
    """
    Receive one data row from simulation, process it, and broadcast state.
    
    Pipeline:
      1. Compute pressure index
      2. Run ML prediction
      3. Classify crush vs surge
      4. Check alert trigger
      5. Store in DB
      6. Broadcast to all WebSocket clients
    """
    row = payload.model_dump()
    location = row["location"]
    timestamp = row.get("timestamp") or datetime.now().isoformat()

    # 1. Compute pressure index
    pressure = compute_pressure_index(row)

    # 2. ML predictions
    ml_result = run_ml_prediction(row)

    # 3. Classify crush vs surge (uses internal history tracking)
    classification = classify_crush_or_surge(location, pressure)

    # 4. Check alert trigger
    should_alert = (
        pressure >= ALERT_THRESHOLD
        and classification == "GENUINE CRUSH BUILDUP"
    )

    # 5. Update in-memory state
    current_state[location] = {
        "location": location,
        "timestamp": timestamp,
        "pressure_index": round(pressure, 2),
        "risk_level": ml_result["risk_level"],
        "crush_window_min": ml_result["crush_window_min"],
        "classification": classification,
        "entry_flow_rate_pax_per_min": row.get("entry_flow_rate_pax_per_min", 0),
        "exit_flow_rate_pax_per_min": row.get("exit_flow_rate_pax_per_min", 0),
        "transport_arrival_burst": row.get("transport_arrival_burst", 0),
        "queue_density_pax_per_m2": row.get("queue_density_pax_per_m2", 0),
        "corridor_width_m": row.get("corridor_width_m", 5),
        "weather": row.get("weather", "Clear"),
        "festival_peak": row.get("festival_peak", 0),
        "vehicle_count": row.get("vehicle_count", 0),
    }

    # Track flow history for charts
    if location not in flow_history:
        flow_history[location] = []
    flow_history[location].append({
        "timestamp": timestamp,
        "entry": row.get("entry_flow_rate_pax_per_min", 0),
        "exit": row.get("exit_flow_rate_pax_per_min", 0),
        "pressure": round(pressure, 2),
    })
    # Keep last 50 readings
    if len(flow_history[location]) > 50:
        flow_history[location] = flow_history[location][-50:]

    # 6. Write to DB
    conn = get_connection()
    try:
        insert_pressure_reading(conn, {
            "timestamp": timestamp,
            "location": location,
            "pressure_index": round(pressure, 2),
            "entry_flow_rate_pax_per_min": row.get("entry_flow_rate_pax_per_min", 0),
            "exit_flow_rate_pax_per_min": row.get("exit_flow_rate_pax_per_min", 0),
            "transport_arrival_burst": row.get("transport_arrival_burst", 0),
            "queue_density_pax_per_m2": row.get("queue_density_pax_per_m2", 0),
            "risk_level": ml_result["risk_level"],
            "crush_window_min": ml_result["crush_window_min"],
        })

        # Handle alert
        alert_created = None
        if should_alert:
            # Check if there's already an active alert for this location
            existing = [a for a in active_alerts if a["location"] == location and a["status"] == "active"]
            if not existing:
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
                    "agency_actions": get_agency_actions(location),
                    "acknowledgements": {},
                }
                active_alerts.append(alert_obj)
                alert_created = alert_obj

                # Log event
                insert_event(conn, "alert_triggered", location, {
                    "pressure_index": round(pressure, 2),
                    "classification": classification,
                    "crush_window_min": ml_result["crush_window_min"],
                    "alert_id": alert_id,
                })
    finally:
        conn.close()

    # 7. Broadcast to all WebSocket clients
    await broadcast_state()

    return {
        "status": "ok",
        "location": location,
        "pressure_index": round(pressure, 2),
        "risk_level": ml_result["risk_level"],
        "crush_window_min": ml_result["crush_window_min"],
        "classification": classification,
        "alert_triggered": alert_created is not None,
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
