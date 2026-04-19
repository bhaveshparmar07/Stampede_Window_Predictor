"""
Pressure Calculator — Computes corridor pressure index from crowd flow metrics.

Core formula weights (sum to 1.0):
  - Net flow (entry - exit): 0.4
  - Queue density: 0.3
  - Transport burst: 0.2
  - Corridor width (inverse): 0.1

Multiplier stack (S1–S11):
  - Festival peak: x1.25
  - Adverse weather: x1.10
  - External event (S1): x1.30
  - Calendar/holiday (S2): x1.15–1.70
  - Aarti timing (S7): x1.25–1.80
  - Auspicious date (S9): x1.50–2.10
  - Combined cap: 2.5x to prevent runaway scores

Additive penalties:
  - Flow conflict (S8): +10 or +20
  - Buffer zone cascade (S5): +8/+15/+25
  - Cluster correction (S11): density override

Post-multiplier modifiers:
  - Corridor obstruction (S10): x1.25/1.6/2.2

Output: clamped to [0, 100]
"""


def compute_pressure_index(row: dict, context: dict = None) -> float:
    """
    Compute the corridor pressure index from a single data row.

    Args:
        row: Dictionary containing flow rates, density, burst, corridor width,
             festival_peak flag, and weather string.
        context: Optional dict with scenario multipliers from context services:
             event_mult, calendar_mult, aarti_mult, auspicious_mult,
             flow_conflict_penalty, buffer_zone_penalty, cluster_zone_density,
             procession_block_pct

    Returns:
        Float pressure index clamped to [0, 100].
    """
    if context is None:
        context = {}

    entry_flow = float(row.get("entry_flow_rate_pax_per_min", 0))
    exit_flow = float(row.get("exit_flow_rate_pax_per_min", 0))
    queue_density = float(row.get("queue_density_pax_per_m2", 0))
    transport_burst = float(row.get("transport_arrival_burst", 0))
    corridor_width = float(row.get("corridor_width_m", 1))

    # ── Core pressure computation ──────────────────────────────────────────
    raw = (
        (entry_flow - exit_flow) * 0.4
        + queue_density * 0.3
        + transport_burst * 0.2
        + (10.0 / max(corridor_width, 0.1)) * 0.1
    )

    # ── S11: Cluster density correction ────────────────────────────────────
    cluster_zone_density = context.get("cluster_zone_density", 0)
    if cluster_zone_density and cluster_zone_density > 0:
        effective_density = max(queue_density, cluster_zone_density * 0.7)
        # Recalculate the density component with the higher effective value
        density_correction = (effective_density - queue_density) * 0.3
        raw += max(density_correction, 0)

    # ── Multiplicative factors ─────────────────────────────────────────────

    # Festival peak multiplier (original)
    festival_peak = row.get("festival_peak", 0)
    festival_mult = 1.25 if int(festival_peak) == 1 else 1.0

    # Weather modifier (original)
    weather = str(row.get("weather", "Clear"))
    weather_mult = 1.10 if weather in ("Rain", "Heat", "Extreme Heat") else 1.0

    # S1: External event multiplier
    event_mult = float(context.get("event_mult", 1.0))

    # S2: Calendar/holiday multiplier
    calendar_mult = float(context.get("calendar_mult", 1.0))

    # S7: Aarti timing multiplier
    aarti_mult = float(context.get("aarti_mult", 1.0))

    # S9: Auspicious date multiplier
    auspicious_mult = float(context.get("auspicious_mult", 1.0))

    # Stack all multipliers with a 2.5x cap to prevent unrealistic scores
    combined_mult = festival_mult * weather_mult * event_mult * calendar_mult * aarti_mult * auspicious_mult
    combined_mult = min(combined_mult, 2.5)

    raw = raw * combined_mult

    # ── Additive penalties ─────────────────────────────────────────────────

    # S8: Flow conflict penalty
    flow_penalty = context.get("flow_conflict_penalty", None)
    if flow_penalty is None:
        flow_penalty = compute_flow_conflict_penalty(entry_flow, exit_flow)
    raw += flow_penalty

    # S5: Buffer zone cascade penalty
    buffer_penalty = float(context.get("buffer_zone_penalty", 0))
    raw += buffer_penalty

    # ── Post-multiplier: S10 corridor obstruction ──────────────────────────
    block_pct = float(context.get("procession_block_pct", 0))
    if block_pct > 0:
        raw = apply_corridor_obstruction(raw, block_pct)

    # ── Clamp to [0, 100] ─────────────────────────────────────────────────
    return min(max(raw, 0), 100)


def compute_flow_conflict_penalty(entry_flow: float, exit_flow: float) -> float:
    """
    S8 — When both flows are high simultaneously, add a crush-risk penalty.
    Worst case: entry_flow > 40 AND exit_flow > 30 in a narrow corridor.
    """
    if entry_flow > 40 and exit_flow > 30:
        return 20   # both flows high — dangerous squeeze
    elif entry_flow > 30 and exit_flow > 20:
        return 10
    return 0


def compute_combined_zone_pressure(primary: float, buffer_pct: float) -> float:
    """
    S5 — Buffer zone feed-forward: when buffer zones are full,
    add penalty to primary corridor pressure.
    """
    if buffer_pct >= 90:
        return 25
    elif buffer_pct >= 80:
        return 15
    elif buffer_pct >= 65:
        return 8
    return 0


def apply_corridor_obstruction(pressure: float, block_pct: float) -> float:
    """
    S10 — When corridor is partially blocked by procession/yatra,
    effective capacity drops and pressure spikes.
    """
    effective_capacity_ratio = (100 - block_pct) / 100
    if effective_capacity_ratio < 0.3:
        return min(pressure * 2.2, 100)  # near-total block
    elif effective_capacity_ratio < 0.5:
        return min(pressure * 1.6, 100)
    elif effective_capacity_ratio < 0.7:
        return min(pressure * 1.25, 100)
    return pressure
