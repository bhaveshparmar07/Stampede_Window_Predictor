"""
SQLite database connection and helpers for Stampede Window Predictor.
"""

import sqlite3
import os
import json
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "stampede.db")
SCHEMA_PATH = os.path.join(os.path.dirname(__file__), "schema.sql")


def get_connection() -> sqlite3.Connection:
    """Get a SQLite connection with row factory enabled."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db():
    """Initialize database by executing schema.sql."""
    conn = get_connection()
    with open(SCHEMA_PATH, "r") as f:
        conn.executescript(f.read())
    conn.close()
    print(f"[DB] Initialized database at {DB_PATH}")


def insert_pressure_reading(conn: sqlite3.Connection, data: dict):
    """Insert a pressure reading row."""
    conn.execute(
        """INSERT INTO pressure_readings 
           (timestamp, location, pressure_index, entry_flow, exit_flow, 
            transport_burst, queue_density, risk_level, crush_window_min)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            data.get("timestamp", datetime.now().isoformat()),
            data["location"],
            data.get("pressure_index", 0),
            data.get("entry_flow_rate_pax_per_min", 0),
            data.get("exit_flow_rate_pax_per_min", 0),
            data.get("transport_arrival_burst", 0),
            data.get("queue_density_pax_per_m2", 0),
            data.get("risk_level", "Low"),
            data.get("crush_window_min", 0),
        ),
    )
    conn.commit()


def insert_alert(conn: sqlite3.Connection, data: dict) -> int:
    """Insert an alert and return its ID."""
    cursor = conn.execute(
        """INSERT INTO alerts 
           (triggered_at, location, pressure_index, risk_classification, 
            crush_window_min, status)
           VALUES (?, ?, ?, ?, ?, 'active')""",
        (
            datetime.now().isoformat(),
            data["location"],
            data["pressure_index"],
            data["classification"],
            data.get("crush_window_min", 0),
        ),
    )
    conn.commit()
    return cursor.lastrowid


def insert_acknowledgement(conn: sqlite3.Connection, data: dict):
    """Record an agency acknowledgement."""
    conn.execute(
        """INSERT INTO acknowledgements 
           (alert_id, agency, acknowledged_at, response_time_sec, action_taken)
           VALUES (?, ?, ?, ?, ?)""",
        (
            data["alert_id"],
            data["agency"],
            datetime.now().isoformat(),
            data.get("response_time_sec", 0),
            data.get("action_taken", ""),
        ),
    )
    conn.commit()


def insert_event(conn: sqlite3.Connection, event_type: str, location: str, details: dict):
    """Write an event to the event log."""
    conn.execute(
        """INSERT INTO event_log (event_type, location, timestamp, details)
           VALUES (?, ?, ?, ?)""",
        (event_type, location, datetime.now().isoformat(), json.dumps(details)),
    )
    conn.commit()


def get_events(conn: sqlite3.Connection, location: str = None, risk_level: str = None, limit: int = 200) -> list:
    """Query event log with optional filters."""
    query = "SELECT * FROM event_log WHERE 1=1"
    params = []

    if location:
        query += " AND location = ?"
        params.append(location)
    if risk_level:
        query += " AND json_extract(details, '$.risk_level') = ?"
        params.append(risk_level)

    query += " ORDER BY timestamp DESC LIMIT ?"
    params.append(limit)

    rows = conn.execute(query, params).fetchall()
    return [dict(row) for row in rows]


def get_active_alerts(conn: sqlite3.Connection) -> list:
    """Get all active (unresolved) alerts."""
    rows = conn.execute(
        "SELECT * FROM alerts WHERE status = 'active' ORDER BY triggered_at DESC"
    ).fetchall()
    return [dict(row) for row in rows]


def get_alert_acknowledgements(conn: sqlite3.Connection, alert_id: int) -> list:
    """Get acknowledgements for a specific alert."""
    rows = conn.execute(
        "SELECT * FROM acknowledgements WHERE alert_id = ? ORDER BY acknowledged_at",
        (alert_id,),
    ).fetchall()
    return [dict(row) for row in rows]
