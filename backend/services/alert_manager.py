"""
Alert Manager — Trigger logic and agency action routing.

Alert triggers when:
  - pressure_index >= ALERT_THRESHOLD (70)
  - AND classification == "GENUINE CRUSH BUILDUP"

Additional alert types (S1–S11):
  - PRE_ARRIVAL_WARNING (S3/S4): transit/toll surge
  - COUNTER_FLOW (S8): bidirectional squeeze
  - ZONE_CASCADE (S5): buffer feeding primary
  - CLUSTER_CRITICAL (S11): nucleation point
  - AARTI_PRESURGE (S7): prayer time approaching
  - PROCESSION_ACTIVE (S10): corridor obstructed
  - TOLL_SURGE (S4): upstream vehicle surge
  - BLACK_SWAN (S6): anomalous z-score spike

Momentary surges above threshold are logged but do NOT trigger full alerts.
"""

from typing import Tuple, Dict, List
from .crush_classifier import classify_crush_or_surge

ALERT_THRESHOLD = 70          # pressure index threshold
PREDICTION_HORIZON_MIN = 10   # target prediction window in minutes
MIN_RISING_READINGS = 5       # for crush confirmation

# ── Agency-specific base actions ──────────────────────────────────────────────

AGENCY_ACTIONS: Dict[str, str] = {
    "police": "Deploy officers to choke point immediately",
    "temple": "Activate darshan hold at inner sanctum gate",
    "transport": "Hold all GSRTC buses at holding zone — no new dispatches",
}

# ── Scenario-specific agency actions ──────────────────────────────────────────

SCENARIO_AGENCY_ACTIONS = {
    "pre_arrival": {
        "police":    "Position crowd control at NH947 entry — convoy arriving in ~14 min",
        "temple":    "Begin pre-emptive queue management — surge incoming",
        "transport": "GSRTC: hold next dispatch batch at Ahmedabad depot",
    },
    "toll_surge": {
        "police":    "Advance notice — vehicle surge at toll. Prepare for crowd increase.",
        "temple":    "Vehicle surge detected upstream. Expect crowd increase in ~22 min.",
        "transport": "Vehicle surge at toll — initiate holding zone now.",
    },
    "counter_flow": {
        "police":    "Implement one-way flow immediately — block entry until exit flow drops below 20 pax/min",
        "temple":    "Announce one-way system via PA — direct exiting devotees to alternate exit gate",
        "transport": "Do not release new bus batch — entry corridor under one-way protocol",
    },
    "zone_cascade": {
        "police":    "Seal market street entry — buffer zone at 85% — stop further inflow",
        "temple":    "Halt darshan token issuance — buffer zones saturated",
        "transport": "Reroute buses to secondary drop point — primary buffer full",
    },
    "cluster_critical": {
        "police":    "Cluster forming at distribution point — deploy officer to disperse immediately",
        "temple":    "Temporarily close distribution counter — crowd compressing dangerously",
        "transport": "No action required — issue is internal to corridor",
    },
    "aarti_presurge": {
        "police":    "Aarti begins soon — position crowd barriers at main entry now",
        "temple":    "Issue pre-aarti capacity advisory — reduce token batch size by 40%",
        "transport": "Hold bus drop-offs for 15 min — aarti surge window beginning",
    },
    "procession_active": {
        "police":    "Procession active — enforce crowd direction on alternate entry path. No new entrants on main corridor.",
        "temple":    "Suspend main entry token issuance for procession duration. Redirect to gate 2.",
        "transport": "All buses to secondary drop zone — main entry corridor obstructed.",
    },
    "black_swan": {
        "police":    "ANOMALY: Unexpected pressure spike — deploy all available units immediately",
        "temple":    "ANOMALY: Suspend all token issuance — situation under review",
        "transport": "ANOMALY: Emergency hold on all dispatches — awaiting assessment",
    },
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


def get_agency_actions(location: str, scenario: str = None) -> List[Dict[str, str]]:
    """
    Generate agency-specific action cards for an alert at the given location.
    If a scenario type is specified, use scenario-specific actions.

    Args:
        location: Corridor location
        scenario: Optional scenario key (e.g. 'pre_arrival', 'counter_flow')

    Returns a list of action dicts, one per agency.
    """
    actions_source = AGENCY_ACTIONS
    if scenario and scenario in SCENARIO_AGENCY_ACTIONS:
        actions_source = SCENARIO_AGENCY_ACTIONS[scenario]

    actions = []
    for agency_key, base_action in actions_source.items():
        actions.append({
            "agency": agency_key,
            "action": f"{base_action} — {location}",
            "acknowledged": False,
            "response_time_sec": None,
            "scenario": scenario or "crush_alert",
        })
    return actions
