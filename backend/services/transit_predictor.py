"""
S3 — In-Transit Crowd on Approach Roads

Predicts choke-point pressure from incoming bus convoy data.
Data tier: Simulated — GSRTC has no open API.
"""

from typing import Dict, List

# In-memory latest transit readings
latest_transit: Dict[str, dict] = {}


def predict_choke_pressure_from_transit(
    vehicles_in_transit: int,
    avg_occupancy: int = 40,         # GSRTC standard bus capacity
    eta_to_choke_min: float = 14,
    corridor_capacity_pax_per_min: float = 50.0,
) -> dict:
    """
    Project corridor pressure from incoming transit vehicles.

    When multiple buses converge simultaneously, the projected inflow
    can exceed corridor absorption capacity, triggering a PRE_ARRIVAL_WARNING.

    Args:
        vehicles_in_transit: Number of buses currently approaching
        avg_occupancy: Average passengers per bus
        eta_to_choke_min: Minutes until convoy reaches the choke point
        corridor_capacity_pax_per_min: Max safe throughput at corridor

    Returns:
        dict with projected_entry_flow, projected_pressure_index, eta_min, alert_tier
    """
    projected_pax = vehicles_in_transit * avg_occupancy
    projected_flow = projected_pax / max(eta_to_choke_min, 1)
    projected_pressure = min((projected_flow / corridor_capacity_pax_per_min) * 100, 100)

    if projected_pressure >= 70:
        tier = "PRE_ARRIVAL_WARNING"
    elif projected_pressure >= 50:
        tier = "ELEVATED_WATCH"
    else:
        tier = "NORMAL"

    return {
        "projected_entry_flow": round(projected_flow, 1),
        "projected_pressure_index": round(projected_pressure, 1),
        "eta_min": eta_to_choke_min,
        "vehicles_in_transit": vehicles_in_transit,
        "projected_pax": projected_pax,
        "alert_tier": tier,
    }


def update_transit_status(corridor: str, transit_data: dict):
    """Store latest transit prediction for a corridor."""
    latest_transit[corridor] = transit_data


def get_transit_status(corridor: str) -> dict:
    """Get latest transit prediction for a corridor."""
    return latest_transit.get(corridor, {})


def get_all_transit_status() -> Dict[str, dict]:
    """Get all latest transit predictions."""
    return dict(latest_transit)
