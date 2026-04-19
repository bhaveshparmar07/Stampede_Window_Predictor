"""
S10 — Religious Procession / Yatra Route Interference

Scheduled processions that physically block corridors.
Data tier: Hardcoded schedule + operator toggle for real-time.
"""

from datetime import datetime, time


PROCESSION_SCHEDULE = {
    "Dwarka": [
        {"name": "Rath Yatra",      "date": "2026-07-04", "start": "09:00", "end": "14:00", "block_pct": 80},
        {"name": "Janmashtami Jhanki", "date": "2026-08-16", "start": "23:00", "end": "02:00", "block_pct": 60},
    ],
    "Ambaji": [
        {"name": "Bhadarvi Poonam", "date": "2026-09-17", "start": "06:00", "end": "10:00", "block_pct": 70},
        {"name": "Navratri Garbi",  "date": "2026-10-05", "start": "20:00", "end": "23:00", "block_pct": 55},
    ],
    "Somnath": [
        {"name": "Kartik Yatra",    "date": "2026-11-11", "start": "07:00", "end": "11:00", "block_pct": 65},
        {"name": "Maha Shivaratri Procession", "date": "2026-02-17", "start": "18:00", "end": "22:00", "block_pct": 75},
    ],
    "Pavagadh": [
        {"name": "Chaitra Navratri Yatra", "date": "2026-03-22", "start": "06:00", "end": "12:00", "block_pct": 50},
    ],
}

# Operator-controlled active processions (can be toggled via API)
active_manual_processions: dict = {}


def get_procession_status(location: str, now: datetime) -> dict:
    """
    Returns active procession details if one is currently underway (scheduled or manual).

    Returns:
        dict with keys: active, name, block_pct, remaining_min
    """
    # Check manual overrides first
    if location in active_manual_processions:
        manual = active_manual_processions[location]
        return {
            "active": True,
            "name": manual.get("name", "Manual procession"),
            "block_pct": manual.get("block_pct", 50),
            "remaining_min": None,
            "is_manual": True,
        }

    # Check scheduled processions
    schedule = PROCESSION_SCHEDULE.get(location, [])
    today_str = now.strftime("%Y-%m-%d")
    current_time = now.time()

    for proc in schedule:
        if proc["date"] != today_str:
            continue

        start = datetime.strptime(proc["start"], "%H:%M").time()
        end = datetime.strptime(proc["end"], "%H:%M").time()

        # Handle overnight processions (end < start)
        if end < start:
            is_active = current_time >= start or current_time <= end
        else:
            is_active = start <= current_time <= end

        if is_active:
            end_min = end.hour * 60 + end.minute
            cur_min = current_time.hour * 60 + current_time.minute
            remaining = end_min - cur_min if end_min > cur_min else 0

            return {
                "active": True,
                "name": proc["name"],
                "block_pct": proc["block_pct"],
                "remaining_min": max(remaining, 0),
            }

    return {"active": False, "name": None, "block_pct": 0, "remaining_min": None}


def apply_corridor_obstruction(pressure: float, block_pct: float) -> float:
    """
    When corridor is partially blocked by procession, effective capacity drops.
    80% block of a 4.2m corridor leaves 0.84m — catastrophic.
    """
    effective_capacity_ratio = (100 - block_pct) / 100
    if effective_capacity_ratio < 0.3:
        return min(pressure * 2.2, 100)  # near-total block
    elif effective_capacity_ratio < 0.5:
        return min(pressure * 1.6, 100)
    elif effective_capacity_ratio < 0.7:
        return min(pressure * 1.25, 100)
    return pressure


def start_manual_procession(location: str, name: str, block_pct: int = 50):
    """Operator-triggered procession start."""
    active_manual_processions[location] = {"name": name, "block_pct": block_pct}


def stop_manual_procession(location: str):
    """Operator-triggered procession end."""
    active_manual_processions.pop(location, None)
