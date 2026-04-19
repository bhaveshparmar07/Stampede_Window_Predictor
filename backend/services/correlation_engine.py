from services.location_registry import LOCATION_REGISTRY

def map_event_to_correlation(venue_type: str, pressure: float, readings: dict) -> dict:
    """
    Translates generic, standalone event pressure into a structure
    that the Temple Pressure Calculator can digest.
    Returns:
        dict containing:
          - compound_mult: to multiply the temple's raw pressure
          - active_signal_count: count of distinct surge indicators
          - ETA_min: how long until the temple feels this impact
    """
    compound_mult = 1.0
    active_sigs = 0
    eta = 999

    if venue_type == "stadium":
        # Stadiums impact temples via dispersal (approaching waves)
        match_status = readings.get("match_status", "ongoing")
        eta = readings.get("dispersal_wave_ETA", 90)

        if match_status == "ended":
            compound_mult += 0.3 if pressure > 70 else 0.1
            active_sigs += 1
        elif match_status == "dispersing":
            compound_mult += 0.5
            active_sigs += 1

        # Check post-match route
        if readings.get("post_match_route") == "NH947":
            compound_mult += 0.2
            active_sigs += 1

    elif venue_type == "procession":
        # Processions act as blockages (corridor_blocked_pct) and direct density
        blocked = readings.get("corridor_blocked_pct", 0)
        eta = readings.get("next_junction_ETA", 10)

        if blocked > 50:
            compound_mult += 0.6
            active_sigs += 1
        elif blocked > 20:
            compound_mult += 0.25
            active_sigs += 1

    elif venue_type == "rally":
        eta = 60
        if pressure > 80:
            compound_mult += 0.4
            active_sigs += 1

    elif venue_type == "social":
        eta = 30
        if pressure > 80:
            compound_mult += 0.45
            active_sigs += 1

    elif venue_type == "strike":
        # Strikes divert traffic to approach paths
        routes = readings.get("blocked_routes", 0)
        div_mult = readings.get("diversion_pressure_multiplier", 1.0)
        eta = 30
        if routes > 0:
            compound_mult = compound_mult * div_mult
            active_sigs += routes

    elif venue_type == "mela":
        eta = 120
        if pressure > 90:
            compound_mult += 0.3
            active_sigs += 1

    return {
        "compound_mult": round(compound_mult, 2),
        "active_signal_count": active_sigs,
        "ETA_min": eta
    }
