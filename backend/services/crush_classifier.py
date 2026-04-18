"""
Crush vs Surge Classifier — Stateful, per-location classification.

Analyzes pressure history to distinguish:
  - GENUINE CRUSH BUILDUP: pressure rising consistently over 3+ readings
  - MOMENTARY SURGE — SELF-RESOLVING: spike followed by drop
  - MONITORING: insufficient data or stable pressure
"""

from typing import Dict, List

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


def get_history(location: str) -> List[float]:
    """Get pressure history for a location."""
    return pressure_history.get(location, [])


def get_all_locations() -> List[str]:
    """Get all locations that have been seen."""
    return list(pressure_history.keys())


def reset_history():
    """Reset all pressure history (for testing)."""
    pressure_history.clear()
