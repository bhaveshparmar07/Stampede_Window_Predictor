"""
Simulation Streamer — Feeds CSV data to the FastAPI backend row by row.

Usage:
  python stream_data.py --speed 2            # 2-second interval
  python stream_data.py --speed 0.5 --location Ambaji
  python stream_data.py --scenario replay    # use replay_scenario.csv
"""

import pandas as pd
import requests
import time
import argparse
import os
import sys
import math

# Default locations — used if CSV lacks a location column
DEFAULT_LOCATIONS = ["Ambaji", "Dwarka", "Somnath", "Pavagadh"]

API_URL = "http://localhost:8000/api/ingest"


def clean_value(v):
    """Convert NaN and numpy types to JSON-safe values."""
    if isinstance(v, float) and (math.isnan(v) or math.isinf(v)):
        return 0
    return v


def main():
    parser = argparse.ArgumentParser(description="Stream CSV data to Stampede Predictor API")
    parser.add_argument("--speed", type=float, default=2.0, help="Seconds between rows (default: 2)")
    parser.add_argument("--location", type=str, default=None, help="Filter to a specific location")
    parser.add_argument("--scenario", type=str, default="live", choices=["live", "replay"],
                        help="'live' for cleaned_dataset.csv, 'replay' for replay_scenario.csv")
    parser.add_argument("--max-rows", type=int, default=None, help="Maximum rows to stream")
    parser.add_argument("--api-url", type=str, default=API_URL, help="API endpoint URL")
    args = parser.parse_args()

    # Determine CSV path
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(script_dir, ".."))

    if args.scenario == "replay":
        csv_path = os.path.join(project_root, "data", "replay_scenario.csv")
    else:
        csv_path = os.path.join(project_root, "data", "cleaned_dataset.csv")

    if not os.path.exists(csv_path):
        print(f"[ERROR] File not found: {csv_path}")
        print("[ERROR] Run 'python backend/models/train_model.py' first to generate cleaned_dataset.csv")
        sys.exit(1)

    # Load CSV
    print(f"[STREAM] Loading {csv_path}")
    df = pd.read_csv(csv_path)
    print(f"[STREAM] Loaded {len(df)} rows")

    # Filter by location if specified
    if args.location:
        if "location" in df.columns:
            df = df[df["location"] == args.location]
            print(f"[STREAM] Filtered to {args.location}: {len(df)} rows")
        else:
            print(f"[STREAM] No 'location' column — will assign {args.location} to all rows")

    # Limit rows
    if args.max_rows:
        df = df.head(args.max_rows)
        print(f"[STREAM] Limited to {args.max_rows} rows")

    print(f"[STREAM] Speed: {args.speed}s between rows")
    print(f"[STREAM] Target: {args.api_url}")
    print(f"[STREAM] Starting in 2 seconds...")
    time.sleep(2)

    # Stream rows
    success_count = 0
    error_count = 0

    for i, (_, row) in enumerate(df.iterrows()):
        payload = {k: clean_value(v) for k, v in row.to_dict().items()}

        # If dataset lacks location column, cycle through defaults
        if "location" not in payload or pd.isna(payload.get("location")):
            if args.location:
                payload["location"] = args.location
            else:
                payload["location"] = DEFAULT_LOCATIONS[i % len(DEFAULT_LOCATIONS)]

        # Ensure timestamp is a string
        if "timestamp" in payload:
            payload["timestamp"] = str(payload["timestamp"])

        try:
            resp = requests.post(args.api_url, json=payload, timeout=10)
            data = resp.json()

            # Pretty print status
            loc = payload["location"]
            pressure = data.get("pressure_index", "?")
            risk = data.get("risk_level", "?")
            classification = data.get("classification", "?")
            alert = "🚨 ALERT!" if data.get("alert_triggered") else ""

            print(
                f"[{i+1}/{len(df)}] {loc:>10} | "
                f"Pressure: {pressure:>6} | "
                f"Risk: {risk:>8} | "
                f"{classification:>35} {alert}"
            )
            success_count += 1

        except requests.exceptions.ConnectionError:
            print(f"[{i+1}/{len(df)}] CONNECTION ERROR — is the backend running on {args.api_url}?")
            error_count += 1
            if error_count > 5:
                print("[STREAM] Too many connection errors. Stopping.")
                break
        except Exception as e:
            print(f"[{i+1}/{len(df)}] ERROR: {e}")
            error_count += 1

        time.sleep(args.speed)

    print(f"\n[STREAM] Done. {success_count} success, {error_count} errors.")


if __name__ == "__main__":
    main()
