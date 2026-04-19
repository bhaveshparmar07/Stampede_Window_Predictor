"""
S9 — Auspicious Date Calendar (Ekadashi, Purnima, Amavasya)

Precomputed 2026 dates from Hindu Panchang with per-location boosts.
Data tier: Hardcoded — deterministic from Hindu lunar calendar.
"""

AUSPICIOUS_DATES_2026 = [
    {"date": "2026-01-10", "type": "ekadashi",    "name": "Pausha Putrada Ekadashi",    "multiplier": 1.55},
    {"date": "2026-01-13", "type": "purnima",     "name": "Pausha Purnima",              "multiplier": 1.65},
    {"date": "2026-01-25", "type": "ekadashi",    "name": "Shattila Ekadashi",           "multiplier": 1.50},
    {"date": "2026-02-08", "type": "purnima",     "name": "Magha Purnima",               "multiplier": 1.60},
    {"date": "2026-02-17", "type": "shivaratri",  "name": "Maha Shivaratri",             "multiplier": 1.90},
    {"date": "2026-02-24", "type": "ekadashi",    "name": "Vijaya Ekadashi",             "multiplier": 1.50},
    {"date": "2026-03-11", "type": "purnima",     "name": "Phalguna Purnima",            "multiplier": 1.65},
    {"date": "2026-03-26", "type": "ekadashi",    "name": "Papmochani Ekadashi",         "multiplier": 1.50},
    {"date": "2026-04-09", "type": "purnima",     "name": "Chaitra Purnima",             "multiplier": 1.60},
    {"date": "2026-04-25", "type": "ekadashi",    "name": "Mohini Ekadashi",             "multiplier": 1.55},
    {"date": "2026-05-08", "type": "purnima",     "name": "Vaishakha Purnima",           "multiplier": 1.65},
    {"date": "2026-05-24", "type": "ekadashi",    "name": "Apara Ekadashi",              "multiplier": 1.50},
    {"date": "2026-06-07", "type": "purnima",     "name": "Jyeshtha Purnima",            "multiplier": 1.60},
    {"date": "2026-06-22", "type": "ekadashi",    "name": "Yogini Ekadashi",             "multiplier": 1.50},
    {"date": "2026-07-07", "type": "purnima",     "name": "Ashadha Purnima (Guru Purnima)", "multiplier": 1.75},
    {"date": "2026-07-22", "type": "ekadashi",    "name": "Kamika Ekadashi",             "multiplier": 1.50},
    {"date": "2026-08-06", "type": "purnima",     "name": "Shravana Purnima (Raksha Bandhan)", "multiplier": 1.70},
    {"date": "2026-08-21", "type": "ekadashi",    "name": "Aja Ekadashi",                "multiplier": 1.50},
    {"date": "2026-09-04", "type": "purnima",     "name": "Bhadrapada Purnima",          "multiplier": 1.65},
    {"date": "2026-09-19", "type": "ekadashi",    "name": "Indira Ekadashi",             "multiplier": 1.55},
    {"date": "2026-10-03", "type": "purnima",     "name": "Ashwin Purnima (Sharad Purnima)", "multiplier": 1.70},
    {"date": "2026-10-18", "type": "ekadashi",    "name": "Prabodhini Ekadashi",         "multiplier": 1.60},
    {"date": "2026-11-02", "type": "purnima",     "name": "Kartik Purnima",              "multiplier": 1.75},
    {"date": "2026-11-17", "type": "ekadashi",    "name": "Utpanna Ekadashi",            "multiplier": 1.50},
    {"date": "2026-12-01", "type": "purnima",     "name": "Margashirsha Purnima",        "multiplier": 1.60},
    {"date": "2026-12-17", "type": "ekadashi",    "name": "Mokshada Ekadashi",           "multiplier": 1.55},
]

# Per-location boosts for specific auspicious types
LOCATION_AUSPICIOUS_BOOST = {
    "Somnath":  {"shivaratri": 2.10, "purnima": 1.75},   # Jyotirlinga — Shivaratri is peak
    "Dwarka":   {"purnima": 1.80, "ekadashi": 1.65},     # Dwadashi Purnima significant
    "Ambaji":   {"purnima": 1.70, "ekadashi": 1.60},
    "Pavagadh": {"ekadashi": 1.55},
}


def get_auspicious_context(location: str, date_str: str) -> dict:
    """
    Returns auspicious date info and multiplier for a given date.
    Applies per-location boost if available.

    Args:
        location: Temple/corridor name
        date_str: Date in YYYY-MM-DD format

    Returns:
        dict with keys: type, name, multiplier
    """
    for entry in AUSPICIOUS_DATES_2026:
        if entry["date"] == date_str:
            # Check for location-specific boost
            boost = LOCATION_AUSPICIOUS_BOOST.get(location, {}).get(entry["type"], None)
            mult = boost if boost else entry["multiplier"]
            return {
                "type": entry["type"],
                "name": entry["name"],
                "multiplier": mult,
            }

    return {"type": "none", "name": None, "multiplier": 1.0}
