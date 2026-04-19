"""
Crush vs Surge Classifier — Stateful, per-location classification.

Analyzes pressure history to distinguish:
  - GENUINE CRUSH BUILDUP: pressure rising consistently over 3+ readings
  - MOMENTARY SURGE — SELF-RESOLVING: spike followed by drop
  - MONITORING: insufficient data or stable pressure

Additional classifiers (S5, S8, S11):
  - Counter-flow detection (S8)
  - Zone cascade detection (S5)
  - Cluster formation detection (S11)
"""

from typing import Dict, List, Optional

# Stateful pressure history — auto-registers new locations
pressure_history: Dict[str, List[float]] = {}

HISTORY_WINDOW = 5       # readings to consider
RISING_THRESHOLD = 3     # minimum consecutive rises for crush confirmation
MAX_HISTORY_LENGTH = 20  # max stored readings per location


def update_history(location: str, new_pressure: float):
    """Append a new pressure reading to the location's history."""
    if location not in pressure_history:
        pressure_history[location] = []

    pressure_history[location].append(new_pressure)

    # Keep only the last MAX_HISTORY_LENGTH readings
    if len(pressure_history[location]) > MAX_HISTORY_LENGTH:
        pressure_history[location] = pressure_history[location][-MAX_HISTORY_LENGTH:]


def classify_crush_or_surge(location: str, new_pressure: float) -> str:
    """
    Classify the current pressure trend for a location.

    Args:
        location: Corridor/location identifier (any string — auto-registered).
        new_pressure: Latest computed pressure index.

    Returns:
        One of: "GENUINE CRUSH BUILDUP", "MOMENTARY SURGE — SELF-RESOLVING", "MONITORING"
    """
    # Update history first
    update_history(location, new_pressure)

    history = pressure_history[location][-HISTORY_WINDOW:]

    if len(history) < 2:
        return "MONITORING"

    # Count how many consecutive readings are rising
    rising_count = sum(
        1 for i in range(1, len(history))
        if history[i] > history[i - 1]
    )

    # Check if the last two readings are dropping
    last_two_dropping = len(history) >= 2 and history[-1] < history[-2]

    if rising_count >= RISING_THRESHOLD and not last_two_dropping:
        return "GENUINE CRUSH BUILDUP"
    elif last_two_dropping:
        return "MOMENTARY SURGE — SELF-RESOLVING"
    else:
        return "MONITORING"


def detect_counter_flow(entry_flow: float, exit_flow: float,
                        corridor_width_m: float = 4.2) -> Optional[str]:
    """
    S8 — Detect bidirectional flow conflict.
    When both directions have high density, a dangerous squeeze forms.

    Args:
        entry_flow: Pax per minute entering corridor
        exit_flow: Pax per minute exiting corridor
        corridor_width_m: Physical corridor width in metres

    Returns:
        Classification string or None if no conflict
    """
    total_flow_density = (entry_flow + exit_flow) / max(corridor_width_m, 0.1)

    if total_flow_density > 18:
        return "COUNTER-FLOW CRITICAL — ENTRY/EXIT COLLISION RISK"
    elif total_flow_density > 12:
        return "COUNTER-FLOW WARNING — SLOW VELOCITY ZONE FORMING"
    return None


def detect_zone_cascade(location: str, buffer_pct: float,
                        primary_pressure: float) -> Optional[str]:
    """
    S5 — Zone cascade: buffer zone feeding primary corridor.
    When buffer is near-full AND primary is already elevated, the cascade is real.

    Returns:
        Classification string or None
    """
    if buffer_pct > 80 and primary_pressure > 55:
        return "ZONE CASCADE — BUFFER FEEDING PRIMARY"
    elif buffer_pct > 70 and primary_pressure > 65:
        return "ZONE CASCADE — APPROACHING CRITICAL"
    return None


def detect_cluster_formation(avg_density: float, density_variance: float,
                             cluster_zone_density: float = 0) -> dict:
    """
    S11 — Detect crowd cluster nucleation at distribution points.
    High variance + high cluster density = stampede nucleation point forming.
    Average density can look safe while a cluster is already dangerous.

    Args:
        avg_density: Average pax/m^2 across corridor
        density_variance: Std dev of density across sub-zones
        cluster_zone_density: Pax/m^2 at hotspot (e.g. prasad counter)

    Returns:
        dict with cluster_flag, cluster_severity, effective_risk
    """
    cluster_flag = False
    cluster_severity = "none"

    if cluster_zone_density > 5.0:
        cluster_flag = True
        cluster_severity = "critical"   # 5+ pax/m^2 is crush threshold
    elif cluster_zone_density > 3.5 and density_variance > 1.5:
        cluster_flag = True
        cluster_severity = "warning"

    return {
        "cluster_flag": cluster_flag,
        "cluster_severity": cluster_severity,
        "effective_risk": "higher_than_average" if density_variance > 1.0 else "uniform",
    }


def get_history(location: str) -> List[float]:
    """Get pressure history for a location."""
    return pressure_history.get(location, [])


def get_all_locations() -> List[str]:
    """Get all locations that have been seen."""
    return list(pressure_history.keys())


def reset_history():
    """Reset all pressure history (for testing)."""
    pressure_history.clear()
