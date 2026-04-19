"""
S2 — Public Holidays & Gazetted Events

Gujarat 2026 holidays + weekend detection.
Data tier: Hardcoded — replace with `holidays` library in production.
"""

from datetime import datetime

GUJARAT_HOLIDAYS_2026 = [
    {"date": "2026-01-26", "name": "Republic Day",         "type": "gazetted_holiday",  "multiplier": 1.40},
    {"date": "2026-03-14", "name": "Holi",                 "type": "state_holiday",     "multiplier": 1.45},
    {"date": "2026-04-10", "name": "Ram Navami",           "type": "state_holiday",     "multiplier": 1.50},
    {"date": "2026-04-14", "name": "Ambedkar Jayanti",     "type": "gazetted_holiday",  "multiplier": 1.20},
    {"date": "2026-05-01", "name": "May Day",              "type": "gazetted_holiday",  "multiplier": 1.15},
    {"date": "2026-08-15", "name": "Independence Day",     "type": "gazetted_holiday",  "multiplier": 1.35},
    {"date": "2026-08-19", "name": "Janmashtami",          "type": "state_holiday",     "multiplier": 1.55},
    {"date": "2026-10-02", "name": "Gandhi Jayanti",       "type": "gazetted_holiday",  "multiplier": 1.30},
    {"date": "2026-10-02", "name": "Navratri Day 1",       "type": "state_holiday",     "multiplier": 1.70},
    {"date": "2026-10-10", "name": "Dussehra",             "type": "gazetted_holiday",  "multiplier": 1.50},
    {"date": "2026-11-01", "name": "Gujarat Foundation Day","type": "state_holiday",     "multiplier": 1.25},
    {"date": "2026-11-04", "name": "Diwali",               "type": "state_holiday",     "multiplier": 1.60},
    {"date": "2026-11-05", "name": "Govardhan Puja",       "type": "state_holiday",     "multiplier": 1.40},
    {"date": "2026-11-19", "name": "Guru Nanak Jayanti",   "type": "gazetted_holiday",  "multiplier": 1.25},
    {"date": "2026-12-25", "name": "Christmas",            "type": "gazetted_holiday",  "multiplier": 1.15},
]


def get_calendar_multiplier(date_str: str) -> dict:
    """
    Returns multiplier and name for a given date (YYYY-MM-DD string).
    Checks holidays first, then weekend.
    """
    for h in GUJARAT_HOLIDAYS_2026:
        if h["date"] == date_str:
            return {
                "multiplier": h["multiplier"],
                "name": h["name"],
                "type": h["type"],
            }

    # Weekend check
    try:
        dow = datetime.strptime(date_str, "%Y-%m-%d").weekday()
        if dow >= 5:
            return {"multiplier": 1.35, "name": "Weekend", "type": "weekend"}
    except ValueError:
        pass

    return {"multiplier": 1.0, "name": "Regular day", "type": "regular"}
