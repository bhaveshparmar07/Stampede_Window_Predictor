"""
S4 — Toll Booth Crowding as Leading Indicator

Toll booth surge ratio calculation for pre-arrival warning.
Data tier: Simulated — NHAI/TPMS has no open data portal.
"""

from typing import Dict, List

TOLL_BOOTHS = {
    "NH947_KHEDBRAHMA": {
        "target_corridor": "Ambaji",
        "distance_km": 30,
        "avg_transit_time_min": 22,
        "baseline_vehicles_per_min": 8.0,
        "highway": "NH947",
    },
    "SH41_CHOTILA": {
        "target_corridor": "Somnath",
        "distance_km": 55,
        "avg_transit_time_min": 40,
        "baseline_vehicles_per_min": 5.0,
        "highway": "SH41",
    },
    "NH48_VADODARA": {
        "target_corridor": "Pavagadh",
        "distance_km": 45,
        "avg_transit_time_min": 35,
        "baseline_vehicles_per_min": 6.0,
        "highway": "NH48",
    },
    "NH47_RAJKOT": {
        "target_corridor": "Dwarka",
        "distance_km": 90,
        "avg_transit_time_min": 60,
        "baseline_vehicles_per_min": 4.0,
        "highway": "NH47",
    },
}

# In-memory latest toll readings
latest_toll_readings: Dict[str, dict] = {}


def compute_toll_surge_ratio(booth_id: str, current_vpm: float) -> dict:
    """
    Compute surge ratio at a toll booth and determine alert tier.

    Args:
        booth_id: Toll booth identifier (e.g. 'NH947_KHEDBRAHMA')
        current_vpm: Current vehicles per minute

    Returns:
        dict with surge_ratio, tier, eta_min, target_corridor
    """
    if booth_id not in TOLL_BOOTHS:
        return {"surge_ratio": 1.0, "tier": "NORMAL", "eta_min": 0, "target_corridor": "Unknown"}

    booth = TOLL_BOOTHS[booth_id]
    ratio = current_vpm / booth["baseline_vehicles_per_min"]

    if ratio >= 2.5:
        tier = "PRE_ARRIVAL_WARNING"
    elif ratio >= 1.8:
        tier = "ELEVATED_WATCH"
    else:
        tier = "NORMAL"

    result = {
        "booth_id": booth_id,
        "surge_ratio": round(ratio, 2),
        "tier": tier,
        "eta_min": booth["avg_transit_time_min"],
        "target_corridor": booth["target_corridor"],
        "highway": booth["highway"],
        "current_vpm": round(current_vpm, 2),
        "baseline_vpm": booth["baseline_vehicles_per_min"],
    }

    # Store latest reading
    latest_toll_readings[booth_id] = result

    return result


def get_all_toll_status() -> List[dict]:
    """Get latest status for all toll booths with readings."""
    return list(latest_toll_readings.values())


def get_toll_status_for_corridor(corridor: str) -> List[dict]:
    """Get toll booth readings that feed into a specific corridor."""
    return [r for r in latest_toll_readings.values() if r["target_corridor"] == corridor]
