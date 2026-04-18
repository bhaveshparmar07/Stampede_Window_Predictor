"""
Alert Manager — Trigger logic and agency action routing.

Alert triggers when:
  - pressure_index >= ALERT_THRESHOLD (70)
  - AND classification == "GENUINE CRUSH BUILDUP"

Momentary surges above threshold are logged but do NOT trigger full alerts.
"""

from typing import Tuple, Dict, List
from .crush_classifier import classify_crush_or_surge

ALERT_THRESHOLD = 70          # pressure index threshold
PREDICTION_HORIZON_MIN = 10   # target prediction window in minutes
MIN_RISING_READINGS = 5       # for crush confirmation

# Agency-specific action strings
AGENCY_ACTIONS: Dict[str, str] = {
    "police": "Deploy officers to choke point immediately",
    "temple": "Activate darshan hold at inner sanctum gate",
    "transport": "Hold all GSRTC buses at holding zone — no new dispatches",
}


def should_trigger_alert(location: str, pressure: float) -> Tuple[bool, str]:
    """
    Determine whether an alert should be triggered.
    
    Args:
        location: Corridor location identifier.
        pressure: Current computed pressure index.
    
    Returns:
        Tuple of (should_trigger: bool, classification: str)
    """
    classification = classify_crush_or_surge(location, pressure)

    if pressure >= ALERT_THRESHOLD and classification == "GENUINE CRUSH BUILDUP":
        return True, "GENUINE CRUSH BUILDUP"

    if pressure >= ALERT_THRESHOLD and classification == "MOMENTARY SURGE — SELF-RESOLVING":
        return False, "MOMENTARY SURGE — SELF-RESOLVING"

    return False, classification


def get_agency_actions(location: str) -> List[Dict[str, str]]:
    """
    Generate agency-specific action cards for an alert at the given location.
    
    Returns a list of action dicts, one per agency.
    """
    actions = []
    for agency_key, base_action in AGENCY_ACTIONS.items():
        actions.append({
            "agency": agency_key,
            "action": f"{base_action} — {location}",
            "acknowledged": False,
            "response_time_sec": None,
        })
    return actions
