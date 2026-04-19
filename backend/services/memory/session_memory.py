from collections import deque
from typing import Dict

MAX_PER_LOCATION = 10

# In-process session store — reset when server restarts
_session_buffer: Dict[str, deque] = {}

def init_session_memory(locations: list[str]):
    for loc in locations:
        _session_buffer[loc] = deque(maxlen=MAX_PER_LOCATION)

def add_event_to_session(location: str, event_summary: str):
    if location not in _session_buffer:
        _session_buffer[location] = deque(maxlen=MAX_PER_LOCATION)
    _session_buffer[location].append(event_summary)

def get_session_memory(location: str) -> str:
    entries = list(_session_buffer.get(location, []))
    if not entries:
        return "No events recorded this session."
    return "\n".join(f"- {e}" for e in entries)

def summarize_resolved_alert(location: str, peak_pressure: float,
                              classification: str, resolution_time_min: float,
                              primary_signal: str, timestamp: str) -> str:
    summary = (f"[{timestamp}] Pressure peaked at {peak_pressure:.1f} "
               f"({classification}) — resolved in {resolution_time_min:.1f} min. "
               f"Primary signal: {primary_signal}.")
    add_event_to_session(location, summary)
    return summary
