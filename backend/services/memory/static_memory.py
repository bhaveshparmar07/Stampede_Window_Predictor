LOCATION_BASELINE_CONTEXT = {
    "Ambaji": """
Ambaji receives 3–5 lakh pilgrims during Navratri, concentrated 18:00–22:00 IST.
Main entry corridor narrows to 4.2m at Saraswati Gate. Typical peak pressure: 65–75.
Sandhya Aarti at 18:30 is the single highest daily surge point — pressure reliably reaches 70–78 during this window.
Historical risk: Navratri 2022 — pressure reached 88, resolved in 14 min after police deployment.
Key crush precursor: transport_arrival_burst > 25 combined with queue_density > 3.5.
Counter-flow most dangerous during Sandhya Aarti exit when new pilgrims still entering.
""",
    "Dwarka": """
Dwarkadhish Temple peak crowds: Janmashtami (Aug) and Kartik Purnima (Nov).
Gomati Ghat creates a 3.8m bottleneck during evening aarti at 19:00.
VIP convoy arrivals cause sudden crowd compression as security cordons reduce public corridor width.
Flash crowds form when Gomati River boat service disembarks simultaneously with aarti timing.
""",
    "Somnath": """
Jyotirlinga site — Maha Shivaratri (Feb) sees 2× normal Navratri attendance.
Sound and Light show at 19:30 creates exit surge that collides with late arrivals — prime counter-flow window.
Sea-facing corridor at 3.6m width; high-tide alerts historically correlated with crowd compression.
Post-show dispersal (21:00–22:00) is highest-risk window of any non-festival day.
""",
    "Pavagadh": """
Hilltop temple — ropeway capacity bottleneck (250 pax/hr) is the primary constraint.
Cable car technical failure causes instant 3× pressure surge at ground entry as crowd cannot ascend.
Navratri Day 5 and Day 9 are peak crush-risk days based on pilgrimage tradition.
Weather risk: monsoon approach roads become slippery — crowd movement slows 40%, increasing compression.
""",
}

def get_static_memory(location: str) -> str:
    return LOCATION_BASELINE_CONTEXT.get(location, "No prior context available for this location.")
