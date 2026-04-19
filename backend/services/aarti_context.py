"""
S7 — Aarti / Prayer Time Surge

Per-temple aarti schedule with multipliers.
Data tier: CCTV-native + Hardcoded schedule.
"""

from datetime import datetime, time


AARTI_SCHEDULE = {
    "Ambaji": [
        {"name": "Mangala",  "time": time(5, 30),  "duration_min": 20, "multiplier": 1.45},
        {"name": "Rajbhog",  "time": time(12, 0),  "duration_min": 15, "multiplier": 1.35},
        {"name": "Sandhya",  "time": time(18, 30), "duration_min": 25, "multiplier": 1.70},  # highest surge
        {"name": "Shayan",   "time": time(21, 0),  "duration_min": 15, "multiplier": 1.30},
    ],
    "Dwarka": [
        {"name": "Mangala",  "time": time(6, 30),  "duration_min": 20, "multiplier": 1.50},
        {"name": "Rajbhog",  "time": time(12, 30), "duration_min": 20, "multiplier": 1.40},
        {"name": "Sandhya",  "time": time(19, 0),  "duration_min": 30, "multiplier": 1.75},
        {"name": "Shayan",   "time": time(21, 30), "duration_min": 20, "multiplier": 1.35},
    ],
    "Somnath": [
        {"name": "Pratah",   "time": time(6, 0),   "duration_min": 30, "multiplier": 1.45},
        {"name": "Madhyan",  "time": time(12, 0),  "duration_min": 20, "multiplier": 1.30},
        {"name": "Sandhya",  "time": time(19, 30), "duration_min": 30, "multiplier": 1.80},  # Light & Sound show
        {"name": "Shayan",   "time": time(22, 0),  "duration_min": 20, "multiplier": 1.25},
    ],
    "Pavagadh": [
        {"name": "Mangala",  "time": time(6, 0),   "duration_min": 20, "multiplier": 1.40},
        {"name": "Madhyan",  "time": time(12, 30), "duration_min": 15, "multiplier": 1.30},
        {"name": "Sandhya",  "time": time(18, 0),  "duration_min": 25, "multiplier": 1.65},
        {"name": "Shayan",   "time": time(20, 30), "duration_min": 15, "multiplier": 1.25},
    ],
}


# Manual overrides
manual_aarti: dict[str, dict] = {}  # location -> aarti_info

def start_manual_aarti(location: str, name: str = "Manual", multiplier: float = 1.6):
    manual_aarti[location] = {
        "aarti_active": True,
        "aarti_name": name,
        "multiplier": multiplier,
        "minutes_to_next": 0,
        "is_manual": True
    }

def stop_manual_aarti(location: str):
    if location in manual_aarti:
        del manual_aarti[location]

def get_aarti_context(location: str, now: datetime) -> dict:
    """
    Returns aarti status and multiplier for the current time.
    Also returns minutes_to_next_aarti for pre-surge elevation.

    Returns:
        dict with keys: aarti_active, aarti_name, multiplier, minutes_to_next
    """
    # Check manual override first
    if location in manual_aarti:
        return manual_aarti[location]

    schedule = AARTI_SCHEDULE.get(location, [])
    current_time = now.time()
    current_min = current_time.hour * 60 + current_time.minute

    best_next = None
    best_dist = 9999

    for aarti in schedule:
        start = aarti["time"]
        start_min = start.hour * 60 + start.minute
        end_min = start_min + aarti["duration_min"]

        # Active window — currently during aarti
        if start_min <= current_min <= end_min:
            return {
                "aarti_active": True,
                "aarti_name": aarti["name"],
                "multiplier": aarti["multiplier"],
                "minutes_to_next": 0,
            }

        # Track nearest upcoming aarti
        dist = start_min - current_min
        if dist > 0 and dist < best_dist:
            best_dist = dist
            best_next = aarti

    # Pre-aarti window (10 min before)
    if best_next and best_dist <= 10:
        return {
            "aarti_active": False,
            "aarti_name": best_next["name"],
            "multiplier": best_next["multiplier"] * 0.85,  # partial pre-surge
            "minutes_to_next": best_dist,
        }

    return {
        "aarti_active": False,
        "aarti_name": None,
        "multiplier": 1.0,
        "minutes_to_next": best_dist if best_next else None,
    }
