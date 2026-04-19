from dataclasses import dataclass, field
from typing import Optional

@dataclass
class MonitoredLocation:
    """
    Unified definition for any monitored crowd location.
    venue_type determines which form factors apply.
    correlated_temples lists temples this entity can affect.
    correlation_radius_km is the threshold for correlation.
    """
    id:                   str             # unique slug, e.g. "ambaji_temple", "nm_stadium_ipl"
    name:                 str             # display name
    venue_type:           str             # temple | stadium | procession | rally | social | strike | mela
    lat:                  float
    lng:                  float
    correlated_temples:   list       # temple location names this entity can affect
    correlation_radius_km: float          # crowd flows toward temples within this radius
    form_factors:         list       # which metrics this entity tracks
    is_scheduled:         bool = True     # False = detected dynamically (flash events)
    active:               bool = True

LOCATION_REGISTRY: list = [

    # ── TEMPLES (permanent) ──────────────────────────────────────────────────
    MonitoredLocation(
        id="ambaji_temple", name="Ambaji", venue_type="temple",
        lat=24.3338, lng=72.8522,
        correlated_temples=[], correlation_radius_km=0,
        form_factors=["pressure_index","entry_flow","exit_flow","queue_density",
                      "corridor_width","aarti_timing","darshan_tokens",
                      "buffer_zones","toll_approach"],
    ),
    MonitoredLocation(
        id="dwarka_temple", name="Dwarka", venue_type="temple",
        lat=22.2442, lng=68.9685,
        correlated_temples=[], correlation_radius_km=0,
        form_factors=["pressure_index","entry_flow","exit_flow","queue_density",
                      "corridor_width","aarti_timing","darshan_tokens","ghat_density"],
    ),
    MonitoredLocation(
        id="somnath_temple", name="Somnath", venue_type="temple",
        lat=20.8880, lng=70.4012,
        correlated_temples=[], correlation_radius_km=0,
        form_factors=["pressure_index","entry_flow","exit_flow","queue_density",
                      "corridor_width","aarti_timing","sound_light_show_timing"],
    ),
    MonitoredLocation(
        id="pavagadh_temple", name="Pavagadh", venue_type="temple",
        lat=22.4693, lng=73.5268,
        correlated_temples=[], correlation_radius_km=0,
        form_factors=["pressure_index","entry_flow","exit_flow","queue_density",
                      "ropeway_capacity","ropeway_status","approach_path_density"],
    ),

    # ── STADIUMS / ARENAS (scheduled events) ─────────────────────────────────
    MonitoredLocation(
        id="nm_stadium_ahmedabad", name="NM Stadium · Ahmedabad",
        venue_type="stadium",
        lat=23.0900, lng=72.5950,
        correlated_temples=["Ambaji"],          # post-match crowd flows on NH947 toward Ambaji
        correlation_radius_km=200,
        form_factors=["gate_flow_pax_min","parking_fill_pct","concourse_density",
                      "match_status","expected_attendance","dispersal_wave_ETA",
                      "post_match_route"],
    ),
    MonitoredLocation(
        id="gmdc_ground_ahmedabad", name="GMDC Ground · Ahmedabad",
        venue_type="stadium",
        lat=23.0448, lng=72.5550,
        correlated_temples=["Ambaji","Dwarka"],
        correlation_radius_km=200,
        form_factors=["gate_flow_pax_min","parking_fill_pct","event_type",
                      "estimated_attendance","dispersal_wave_ETA"],
    ),

    # ── PROCESSIONS (scheduled, route-based) ─────────────────────────────────
    MonitoredLocation(
        id="rath_yatra_dwarka", name="Rath Yatra · Dwarka",
        venue_type="procession",
        lat=22.2390, lng=68.9650,
        correlated_temples=["Dwarka"],          # route passes through temple entry corridor
        correlation_radius_km=1,
        form_factors=["route_segment_density","march_velocity_m_per_min",
                      "next_junction_ETA","route_progress_pct",
                      "corridor_blocked_pct","procession_length_m"],
    ),
    MonitoredLocation(
        id="bhadarvi_poonam_ambaji", name="Bhadarvi Poonam · Ambaji",
        venue_type="procession",
        lat=24.3310, lng=72.8510,
        correlated_temples=["Ambaji"],
        correlation_radius_km=1,
        form_factors=["route_segment_density","march_velocity_m_per_min",
                      "corridor_blocked_pct","procession_duration_remaining"],
    ),

    # ── POLITICAL RALLIES (scheduled, may be spontaneous) ────────────────────
    MonitoredLocation(
        id="rally_placeholder", name="Political Rally · TBD",
        venue_type="rally",
        lat=0, lng=0,                           # set dynamically when rally is registered
        correlated_temples=[],                  # computed at registration time
        correlation_radius_km=500,              # 500m — shared approach roads
        form_factors=["stage_perimeter_density","crowd_radius_m",
                      "estimated_attendance","scheduled_end_time",
                      "exit_route_capacity","security_perimeter_m"],
        is_scheduled=False,
    ),

    # ── SOCIAL / FLASH GATHERINGS (often unscheduled) ────────────────────────
    MonitoredLocation(
        id="social_placeholder", name="Social Gathering · TBD",
        venue_type="social",
        lat=0, lng=0,
        correlated_temples=[],
        correlation_radius_km=1000,             # 1km — route overlap
        form_factors=["area_coverage_m2","crowd_density_pax_m2",
                      "crowd_velocity_m_min","flash_factor",
                      "social_trigger_type","nearest_choke_point"],
        is_scheduled=False,
    ),

    # ── STRIKES / ROAD DISRUPTIONS (negative pressure — blockages) ───────────
    MonitoredLocation(
        id="strike_placeholder", name="Road Disruption · TBD",
        venue_type="strike",
        lat=0, lng=0,
        correlated_temples=[],
        correlation_radius_km=999,              # any temple on the affected route
        form_factors=["blocked_routes","alternate_route_capacity",
                      "affected_zone_radius_km","disruption_type",
                      "ETA_clearance","diversion_pressure_multiplier"],
        is_scheduled=False,
    ),

    # ── MELAS / FAIRS (scheduled, multi-day) ─────────────────────────────────
    MonitoredLocation(
        id="tarnetar_mela", name="Tarnetar Mela",
        venue_type="mela",
        lat=22.5667, lng=71.9167,
        correlated_temples=[],                  # standalone — no temple within 5km
        correlation_radius_km=5,
        form_factors=["stall_density","entry_exit_ratio","food_court_cluster",
                      "day_of_mela","peak_hours","crowd_capacity_pct"],
    ),
]

def get_temples() -> list:
    return [l for l in LOCATION_REGISTRY if l.venue_type == "temple" and l.active]

def get_active_events() -> list:
    return [l for l in LOCATION_REGISTRY if l.venue_type != "temple" and l.active]

def get_correlated_events(temple_name: str) -> list:
    """Returns all non-temple events that correlate to this temple."""
    return [
        loc for loc in LOCATION_REGISTRY
        if loc.venue_type != "temple"
        and temple_name in loc.correlated_temples
        and loc.active
    ]

def register_dynamic_event(
    name: str, venue_type: str, lat: float, lng: float,
    all_temples: list, radius_km: float, form_factors: list,
) -> MonitoredLocation:
    """
    Called when operator adds a new event (rally, flash gathering, strike)
    from the admin panel at runtime.
    """
    import math
    temple_coords = {
        "Ambaji":   (24.3338, 72.8522),
        "Dwarka":   (22.2442, 68.9685),
        "Somnath":  (20.8880, 70.4012),
        "Pavagadh": (22.4693, 73.5268),
    }
    correlated = []
    for tname, (tlat, tlng) in temple_coords.items():
        dist = math.sqrt((lat - tlat)**2 + (lng - tlng)**2) * 111  # approx km
        if dist <= radius_km:
            correlated.append(tname)

    new_id = f"{venue_type}_{name.lower().replace(' ','_')}"
    existing = next((l for l in LOCATION_REGISTRY if l.id == new_id), None)
    if existing:
        return existing
        
    new_loc = MonitoredLocation(
        id=new_id,
        name=name, venue_type=venue_type,
        lat=lat, lng=lng,
        correlated_temples=correlated,
        correlation_radius_km=radius_km,
        form_factors=form_factors,
        is_scheduled=False,
    )
    LOCATION_REGISTRY.append(new_loc)
    return new_loc
