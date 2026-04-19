import time
import requests
import json
import random
from datetime import datetime

base_url = "http://localhost:8080"
event_id = "nm_stadium_ahmedabad"

def simulate_stadium_match():
    print(f"--- Simulating Stadium Dispersal for {event_id} ---")
    
    # 1. Base State (Match ongoing, 100k people inside)
    payload = {
        "timestamp": datetime.now().isoformat(),
        "readings": {
            "parking_fill_pct": 98,
            "gate_flow_pax_min": 100,
            "concourse_density": 1.2,
            "match_status": "ongoing",
            "expected_attendance": 110000,
            "dispersal_wave_ETA": 120,
            "post_match_route": "NH947"
        }
    }
    print("Match Ongoing. Sending base state...")
    res = requests.post(f"{base_url}/api/ingest/event/{event_id}", json=payload)
    print("Response:", res.json())
    time.sleep(5)
    
    # 2. Match Ends. Dispersal begins
    print("\nMatch ENDS. Gates open, crowds dispersing...")
    payload["readings"]["match_status"] = "ended"
    payload["readings"]["gate_flow_pax_min"] = 1500  # Massive surge at exit
    payload["readings"]["concourse_density"] = 3.5 
    payload["readings"]["dispersal_wave_ETA"] = 90
    
    res = requests.post(f"{base_url}/api/ingest/event/{event_id}", json=payload)
    print("Response:", res.json())
    time.sleep(5)
    
    # 3. Mass evacuation
    print("\nMass Evacuation (15 mins later). Pressure peaking...")
    payload["readings"]["match_status"] = "dispersing"
    payload["readings"]["gate_flow_pax_min"] = 3500 
    payload["readings"]["parking_fill_pct"] = 60
    payload["readings"]["concourse_density"] = 4.2 
    payload["readings"]["dispersal_wave_ETA"] = 60
    
    res = requests.post(f"{base_url}/api/ingest/event/{event_id}", json=payload)
    print("Response:", res.json())
    
    print("\nSimulation complete. Check backend logs and frontend UI to see")
    print("how Ambaji's pressure receives the compound_mult correlation penalty.")

if __name__ == "__main__":
    simulate_stadium_match()
