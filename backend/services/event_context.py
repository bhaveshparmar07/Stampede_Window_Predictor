"""
S1 — IPL / Large Sporting Events Context

Hardcoded IPL 2026 fixtures + get_active_event_context() for pressure multiplier.
Data tier: Hardcoded — replace with BCCI API in production.
"""

from datetime import datetime, timedelta

SCHEDULED_EVENTS = [
    {
        "event_id": "IPL_2026_MI_GT_01",
        "event_type": "cricket_match",
        "venue": "Narendra Modi Stadium, Ahmedabad",
        "start_time": "2026-04-20T19:30:00",
        "expected_attendance": 110000,
        "nearby_corridors": ["Ambaji"],
        "distance_km": 130,
        "dispersal_window_hrs": 2,
    },
    {
        "event_id": "IPL_2026_GT_RCB_02",
        "event_type": "cricket_match",
        "venue": "Narendra Modi Stadium, Ahmedabad",
        "start_time": "2026-04-27T15:30:00",
        "expected_attendance": 110000,
        "nearby_corridors": ["Ambaji"],
        "distance_km": 130,
        "dispersal_window_hrs": 2,
    },
    {
        "event_id": "IPL_2026_GT_CSK_03",
        "event_type": "cricket_match",
        "venue": "Narendra Modi Stadium, Ahmedabad",
        "start_time": "2026-05-04T19:30:00",
        "expected_attendance": 110000,
        "nearby_corridors": ["Ambaji"],
        "distance_km": 130,
        "dispersal_window_hrs": 2,
    },
    {
        "event_id": "IPL_2026_GT_KKR_04",
        "event_type": "cricket_match",
        "venue": "Narendra Modi Stadium, Ahmedabad",
        "start_time": "2026-05-11T15:30:00",
        "expected_attendance": 110000,
        "nearby_corridors": ["Ambaji", "Pavagadh"],
        "distance_km": 130,
        "dispersal_window_hrs": 2,
    },
    {
        "event_id": "NAVRATRI_GARBA_2026",
        "event_type": "mela",
        "venue": "Ahmedabad Riverfront",
        "start_time": "2026-10-02T20:00:00",
        "expected_attendance": 200000,
        "nearby_corridors": ["Ambaji", "Pavagadh"],
        "distance_km": 160,
        "dispersal_window_hrs": 3,
    },
]


def get_active_event_context(location: str, now: datetime) -> dict:
    """
    Returns multiplier and label if a relevant event ends within 4 hours
    and the dispersal crowd could reach this corridor.
    """
    for ev in SCHEDULED_EVENTS:
        if location not in ev["nearby_corridors"]:
            continue

        start = datetime.fromisoformat(ev["start_time"])
        # Assume 3-hour event duration
        end_time = start + timedelta(hours=3)
        dispersal_start = end_time
        dispersal_end = dispersal_start + timedelta(hours=ev["dispersal_window_hrs"])

        if dispersal_start <= now <= dispersal_end:
            return {
                "multiplier": 1.30,
                "label": f"{ev['event_type']} — {ev['venue']}",
                "event_id": ev["event_id"],
                "distance_km": ev["distance_km"],
                "expected_attendance": ev["expected_attendance"],
            }

    return {"multiplier": 1.0, "label": None, "event_id": None, "distance_km": 0, "expected_attendance": 0}
