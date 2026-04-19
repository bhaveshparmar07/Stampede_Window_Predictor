"""
S6 — Uncertain / Black Swan Event Detection

Z-score anomaly detection on pressure_index per location.
Data tier: CCTV-native — works with existing data only.
"""

import statistics
from typing import Dict, List

# Rolling pressure history for anomaly detection (separate from crush classifier history)
anomaly_history: Dict[str, List[float]] = {}
ANOMALY_WINDOW = 50  # rolling window for z-score calculation


def detect_anomaly(location: str, current_pressure: float, history: List[float] = None) -> dict:
    """
    Detect anomalous pressure readings using z-score over a rolling window.

    Args:
        location: Corridor identifier
        current_pressure: Current pressure index
        history: Optional external history (uses internal if None)

    Returns:
        dict with keys: anomaly_flag, z_score, anomaly_severity
    """
    # Use internal history if none provided
    if history is None:
        if location not in anomaly_history:
            anomaly_history[location] = []
        anomaly_history[location].append(current_pressure)
        # Keep rolling window
        if len(anomaly_history[location]) > ANOMALY_WINDOW:
            anomaly_history[location] = anomaly_history[location][-ANOMALY_WINDOW:]
        history = anomaly_history[location]

    if len(history) < 10:
        return {"anomaly_flag": False, "z_score": 0.0, "anomaly_severity": "none"}

    mean = statistics.mean(history)
    std = statistics.stdev(history)

    if std == 0:
        return {"anomaly_flag": False, "z_score": 0.0, "anomaly_severity": "none"}

    z = (current_pressure - mean) / std

    if z > 3.0:
        severity = "critical"
    elif z > 2.0:
        severity = "moderate"
    else:
        severity = "none"

    return {
        "anomaly_flag": z > 2.0,
        "z_score": round(z, 2),
        "anomaly_severity": severity,
    }


def get_ai_triage_mock(location: str, pressure: float, classification: str,
                       anomaly_data: dict, operator_context: str = "") -> str:
    """
    Mock AI triage response for demo (replaces Claude API call).
    Returns a contextual analysis string based on the current situation.
    """
    severity = anomaly_data.get("anomaly_severity", "none")
    z_score = anomaly_data.get("z_score", 0)

    if severity == "critical":
        base = (f"CRITICAL ANOMALY at {location}: pressure {pressure:.0f} is {z_score:.1f} "
                f"standard deviations above normal. This is consistent with a sudden external "
                f"event — possible crowd panic, infrastructure failure, or unscheduled VIP movement. "
                f"Police should act first: deploy crowd control immediately.")
    elif severity == "moderate":
        base = (f"MODERATE ANOMALY at {location}: pressure {pressure:.0f} is elevated "
                f"(z={z_score:.1f}). Pattern suggests unusual crowd buildup — possibly early "
                f"festival arrivals or transport convergence. Temple trust should prepare "
                f"pre-emptive queue management.")
    else:
        base = (f"No anomaly detected at {location}. Pressure {pressure:.0f} is within "
                f"normal operating range. Classification: {classification}. Continue monitoring.")

    if operator_context:
        base += f" Operator note: '{operator_context}' — adjusting risk assessment accordingly."

    return base


# Operator context storage per location
operator_contexts: Dict[str, str] = {}


def set_operator_context(location: str, context: str):
    """Store operator-provided context for AI triage enrichment."""
    operator_contexts[location] = context


def get_operator_context(location: str) -> str:
    """Retrieve current operator context for a location."""
    return operator_contexts.get(location, "")
