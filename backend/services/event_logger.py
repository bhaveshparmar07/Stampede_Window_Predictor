"""
Event Logger — Writes all significant events to the SQLite event_log table.
"""

import json
from ..database import get_connection, insert_event


def log_pressure_reading(location: str, pressure_index: float, risk_level: str, details: dict = None):
    """Log a pressure reading event."""
    conn = get_connection()
    try:
        event_details = {
            "pressure_index": pressure_index,
            "risk_level": risk_level,
            **(details or {}),
        }
        insert_event(conn, "pressure_reading", location, event_details)
    finally:
        conn.close()


def log_alert_triggered(location: str, pressure_index: float, classification: str, crush_window_min: float):
    """Log an alert trigger event."""
    conn = get_connection()
    try:
        insert_event(conn, "alert_triggered", location, {
            "pressure_index": pressure_index,
            "classification": classification,
            "crush_window_min": crush_window_min,
        })
    finally:
        conn.close()


def log_acknowledgement(location: str, agency: str, response_time_sec: int, alert_id: int):
    """Log an agency acknowledgement event."""
    conn = get_connection()
    try:
        insert_event(conn, "acknowledgement", location, {
            "agency": agency,
            "response_time_sec": response_time_sec,
            "alert_id": alert_id,
        })
    finally:
        conn.close()


def log_replay_event(event_type: str, details: dict):
    """Log a replay-related event."""
    conn = get_connection()
    try:
        insert_event(conn, f"replay_{event_type}", details.get("location", "system"), details)
    finally:
        conn.close()
