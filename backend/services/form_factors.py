"""
Form factors define what metrics each venue type collects and how they map
to a pressure-equivalent score (0–100) for the dashboard gauge.
"""

FORM_FACTOR_SCHEMA = {

    "temple": {
        "pressure_metric":  "pressure_index",        # 0–100, computed by existing formula
        "primary_signals":  ["entry_flow","exit_flow","queue_density","corridor_width"],
        "context_signals":  ["aarti_timing","calendar_mult","festival_peak"],
        "approach_signals": ["toll_approach","transit_approach","buffer_zones"],
        "gauge_label":      "Corridor pressure",
        "gauge_unit":       "/ 100",
        "agency_actions":   True,                    # shows police/temple/transport cards
        "crush_window":     True,                    # shows countdown timer
        "aarti_countdown":  True,
    },

    "stadium": {
        "pressure_metric":  "fill_pressure",         # derived from attendance/capacity
        "primary_signals":  ["gate_flow_pax_min","parking_fill_pct","concourse_density"],
        "context_signals":  ["match_status","expected_attendance"],
        "approach_signals": ["dispersal_wave_ETA","post_match_route"],
        "gauge_label":      "Venue fill",
        "gauge_unit":       "%",
        "agency_actions":   False,                   # stadium has its own security
        "crush_window":     False,
        "aarti_countdown":  False,
        "correlated_view":  True,                    # shows "Ambaji receives in X min"
    },

    "procession": {
        "pressure_metric":  "route_density_score",   # crowd/route_width at densest segment
        "primary_signals":  ["route_segment_density","march_velocity_m_per_min",
                             "corridor_blocked_pct"],
        "context_signals":  ["procession_length_m","next_junction_ETA"],
        "approach_signals": [],
        "gauge_label":      "Route density",
        "gauge_unit":       "/ 100",
        "agency_actions":   False,
        "crush_window":     False,
        "aarti_countdown":  False,
        "moving_entity":    True,                    # location changes over time
        "correlated_view":  True,
    },

    "rally": {
        "pressure_metric":  "perimeter_pressure",    # stage_perimeter_density × crowd_radius
        "primary_signals":  ["stage_perimeter_density","crowd_radius_m","estimated_attendance"],
        "context_signals":  ["scheduled_end_time","security_perimeter_m"],
        "approach_signals": ["exit_route_capacity"],
        "gauge_label":      "Crowd density",
        "gauge_unit":       "/ 100",
        "agency_actions":   False,
        "crush_window":     False,
        "aarti_countdown":  False,
        "correlated_view":  True,
    },

    "social": {
        "pressure_metric":  "flash_pressure",        # density × flash_factor
        "primary_signals":  ["crowd_density_pax_m2","area_coverage_m2","crowd_velocity_m_min"],
        "context_signals":  ["social_trigger_type","flash_factor"],
        "approach_signals": ["nearest_choke_point"],
        "gauge_label":      "Flash crowd intensity",
        "gauge_unit":       "/ 100",
        "agency_actions":   False,
        "crush_window":     False,
        "aarti_countdown":  False,
        "black_swan":       True,                    # always use AI triage for social events
        "correlated_view":  True,
    },

    "strike": {
        "pressure_metric":  "disruption_score",      # blockage × affected_zone
        "primary_signals":  ["blocked_routes","alternate_route_capacity",
                             "affected_zone_radius_km"],
        "context_signals":  ["disruption_type","ETA_clearance"],
        "approach_signals": [],
        "gauge_label":      "Disruption severity",
        "gauge_unit":       "/ 100",
        "agency_actions":   False,
        "crush_window":     False,
        "aarti_countdown":  False,
        "inverse_pressure": True,                    # blockage reduces flow = increases compression elsewhere
        "correlated_view":  True,
        "black_swan":       True,
    },

    "mela": {
        "pressure_metric":  "mela_crowd_pressure",   # entry_exit_ratio × crowd_capacity_pct
        "primary_signals":  ["stall_density","entry_exit_ratio","food_court_cluster"],
        "context_signals":  ["day_of_mela","peak_hours"],
        "approach_signals": [],
        "gauge_label":      "Ground occupancy",
        "gauge_unit":       "%",
        "agency_actions":   False,
        "crush_window":     False,
        "aarti_countdown":  False,
    },
}

def get_form_factor(venue_type: str) -> dict:
    return FORM_FACTOR_SCHEMA.get(venue_type, FORM_FACTOR_SCHEMA["temple"])

def compute_generic_pressure(venue_type: str, readings: dict) -> float:
    """
    Computes a 0–100 pressure score for any venue type from its readings.
    Temple pressure uses the existing pressure_calculator.py formula.
    All others use simplified linear scaling appropriate to their form factor.
    """
    if venue_type == "temple":
        raise ValueError("Use pressure_calculator.py for temples")

    elif venue_type == "stadium":
        fill = readings.get("parking_fill_pct", 50)
        gate = readings.get("gate_flow_pax_min", 0)
        concourse = readings.get("concourse_density", 1.0)
        return min((fill * 0.5 + gate * 0.3 + concourse * 10 * 0.2), 100)

    elif venue_type == "procession":
        density = readings.get("route_segment_density", 2.0)
        blocked = readings.get("corridor_blocked_pct", 0)
        vel     = readings.get("march_velocity_m_per_min", 30)
        # Low velocity + high density + high block = high pressure
        return min(density * 15 + blocked * 0.3 + max(0, (30 - vel)), 100)

    elif venue_type == "rally":
        perimeter = readings.get("stage_perimeter_density", 2.0)
        radius    = readings.get("crowd_radius_m", 100)
        return min(perimeter * 15 + (radius / 500) * 30, 100)

    elif venue_type == "social":
        density  = readings.get("crowd_density_pax_m2", 1.0)
        flash    = readings.get("flash_factor", 1.0)
        return min(density * 15 * flash, 100)

    elif venue_type == "strike":
        routes_blocked = readings.get("blocked_routes", 0)  # count
        zone_km        = readings.get("affected_zone_radius_km", 1)
        return min(routes_blocked * 20 + zone_km * 5, 100)

    elif venue_type == "mela":
        capacity_pct = readings.get("crowd_capacity_pct", 50)
        er_ratio     = readings.get("entry_exit_ratio", 1.0)
        return min(capacity_pct * 0.7 + er_ratio * 15, 100)

    return 50.0
