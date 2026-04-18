"""
Pressure Calculator — Computes corridor pressure index from crowd flow metrics.

Formula weights (sum to 1.0):
  - Net flow (entry - exit): 0.4
  - Queue density: 0.3
  - Transport burst: 0.2
  - Corridor width (inverse): 0.1

Multipliers:
  - Festival peak: ×1.25
  - Adverse weather (Rain/Heat): ×1.10

Output: clamped to [0, 100]
"""


def compute_pressure_index(row: dict) -> float:
    """
    Compute the corridor pressure index from a single data row.
    
    Args:
        row: Dictionary containing flow rates, density, burst, corridor width,
             festival_peak flag, and weather string.
    
    Returns:
        Float pressure index clamped to [0, 100].
    """
    entry_flow = float(row.get("entry_flow_rate_pax_per_min", 0))
    exit_flow = float(row.get("exit_flow_rate_pax_per_min", 0))
    queue_density = float(row.get("queue_density_pax_per_m2", 0))
    transport_burst = float(row.get("transport_arrival_burst", 0))
    corridor_width = float(row.get("corridor_width_m", 1))

    # Core pressure computation with weighted components
    raw = (
        (entry_flow - exit_flow) * 0.4
        + queue_density * 0.3
        + transport_burst * 0.2
        + (10.0 / max(corridor_width, 0.1)) * 0.1
    )

    # Festival peak multiplier
    festival_peak = row.get("festival_peak", 0)
    festival_mult = 1.25 if int(festival_peak) == 1 else 1.0

    # Weather modifier
    weather = str(row.get("weather", "Clear"))
    weather_mult = 1.10 if weather in ("Rain", "Heat", "Extreme Heat") else 1.0

    # Clamp to [0, 100]
    return min(max(raw * festival_mult * weather_mult, 0), 100)
