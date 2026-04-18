"""
Replay Scenario Generator — Creates a pre-built near-crush sequence.

Generates ~90 rows simulating pressure building from ~30 to ~85+ at Ambaji,
with labeled event phases for replay mode demonstration.
"""

import os
import pandas as pd
import numpy as np

def generate_replay_scenario():
    """Generate a realistic near-crush replay scenario."""
    np.random.seed(42)
    
    n_frames = 90
    frames = []
    
    # Pressure curve: starts low (~30), builds gradually, peaks at ~85-90
    # Phases: normal → surge_start → crush_build → peak → alert_fired → acknowledged
    base_pressure_curve = np.concatenate([
        np.linspace(28, 35, 15) + np.random.normal(0, 2, 15),     # normal
        np.linspace(35, 50, 15) + np.random.normal(0, 3, 15),     # starting to build
        np.linspace(50, 65, 15) + np.random.normal(0, 2, 15),     # surge_start
        np.linspace(65, 78, 15) + np.random.normal(0, 2, 15),     # crush_build
        np.linspace(78, 88, 15) + np.random.normal(0, 1.5, 15),   # peak
        np.linspace(88, 75, 15) + np.random.normal(0, 2, 15),     # post-alert response
    ])
    
    for i in range(n_frames):
        pressure = max(0, min(100, base_pressure_curve[i]))
        
        # Determine event label based on phase
        if i < 15:
            event_label = "normal"
        elif i < 30:
            event_label = "building"
        elif i < 45:
            event_label = "surge_start"
        elif i < 55:
            event_label = "crush_build"
        elif i == 55:
            event_label = "classifier_fires"
        elif i < 60:
            event_label = "crush_build"
        elif i == 60:
            event_label = "alert_fired"
        elif i == 65:
            event_label = "acknowledged_police"
        elif i == 68:
            event_label = "acknowledged_temple"
        elif i == 70:
            event_label = "acknowledged_transport"
        elif i < 75:
            event_label = "peak"
        else:
            event_label = "resolving"
        
        # Derive features from pressure (reverse-engineered to be realistic)
        entry_flow = 40 + pressure * 1.8 + np.random.normal(0, 5)
        exit_flow = max(10, entry_flow * (0.6 - pressure * 0.002) + np.random.normal(0, 8))
        transport_burst = 1 if pressure > 50 and np.random.random() > 0.4 else 0
        vehicle_count = int(3 + pressure * 0.08 + np.random.normal(0, 1))
        queue_density = max(0.5, pressure * 0.06 + np.random.normal(0, 0.3))
        
        # Higher pressure → narrower corridors in the scenario
        corridor_width = 3 if i > 30 else 5
        
        # Determine risk level from pressure
        if pressure < 40:
            risk_level = "Low"
        elif pressure < 55:
            risk_level = "Moderate"
        elif pressure < 70:
            risk_level = "High"
        else:
            risk_level = "Critical"
        
        # Crush window decreases as pressure builds
        crush_window = max(1, int(20 - pressure * 0.15 + np.random.normal(0, 1)))
        
        frames.append({
            "frame_index": i,
            "timestamp": f"2026-04-18T{10 + i//30:02d}:{(i*2)%60:02d}:00",
            "location": "Ambaji",
            "corridor_width_m": corridor_width,
            "entry_flow_rate_pax_per_min": round(max(0, entry_flow), 2),
            "exit_flow_rate_pax_per_min": round(max(0, exit_flow), 2),
            "transport_arrival_burst": transport_burst,
            "vehicle_count": max(0, vehicle_count),
            "queue_density_pax_per_m2": round(max(0, queue_density), 2),
            "weather": "Heat",
            "festival_peak": 1,
            "pressure_index": round(pressure, 2),
            "risk_level": risk_level,
            "predicted_crush_window": crush_window,
            "event_label": event_label,
        })
    
    return pd.DataFrame(frames)


if __name__ == "__main__":
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(script_dir, ".."))
    output_path = os.path.join(project_root, "data", "replay_scenario.csv")
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    df = generate_replay_scenario()
    df.to_csv(output_path, index=False)
    
    print(f"[REPLAY] Generated {len(df)} frames")
    print(f"[REPLAY] Saved to {output_path}")
    print(f"[REPLAY] Pressure range: {df['pressure_index'].min():.1f} -> {df['pressure_index'].max():.1f}")
    print(f"[REPLAY] Event labels: {df['event_label'].unique().tolist()}")
