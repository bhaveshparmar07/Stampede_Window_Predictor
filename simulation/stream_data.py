"""
Simulation Streamer — Feeds CSV data to the FastAPI backend row by row.

Usage:
  python stream_data.py --speed 2
  python stream_data.py --speed 0.5 --location Ambaji
  python stream_data.py --scenario replay
  python stream_data.py --csv ../data/cleaned_dataset_augmented.csv

Environment:
  STAMPEDE_API_URL  Full ingest URL (default: http://localhost:8080/api/ingest)
  STREAM_CSV        Override path to live corridor CSV when not using --csv
"""

from __future__ import annotations

import argparse
import json
import math
import os
import sys
import time

import pandas as pd
import requests

DEFAULT_LOCATIONS = ["Ambaji", "Dwarka", "Somnath", "Pavagadh"]


def default_api_url() -> str:
    return os.environ.get("STAMPEDE_API_URL", "http://localhost:8080/api/ingest").strip()


def clean_value(v):
    """Convert NaN / numpy / pandas scalars to JSON-safe values."""
    if v is None:
        return None
    try:
        if pd.isna(v):
            return None
    except (TypeError, ValueError):
        pass
    if isinstance(v, float) and (math.isnan(v) or math.isinf(v)):
        return 0
    if hasattr(v, "item") and not isinstance(v, (bytes, str, dict, list)):
        try:
            v = v.item()
        except Exception:
            pass
    if isinstance(v, (int, float, str, bool)):
        return v
    return str(v)


def resolve_live_csv(project_root: str, explicit_csv: str | None) -> str:
    if explicit_csv:
        return explicit_csv if os.path.isabs(explicit_csv) else os.path.normpath(os.path.join(os.getcwd(), explicit_csv))

    env_csv = os.environ.get("STREAM_CSV", "").strip()
    if env_csv:
        return env_csv if os.path.isabs(env_csv) else os.path.normpath(os.path.join(project_root, env_csv))

    aug = os.path.join(project_root, "data", "corridor_readings_augmented.csv")
    if os.path.exists(aug):
        return aug

    cleaned = os.path.join(project_root, "data", "cleaned_dataset_augmented.csv")
    if os.path.exists(cleaned):
        print(f"[STREAM] Using {cleaned} (augmented file not found)")
        return cleaned

    return aug


def handle_ingest_response(resp: requests.Response, index: int, total: int, loc: str) -> bool:
    """Parse JSON or print a clear error when the server returns HTML/text."""
    if not resp.ok:
        snippet = (resp.text or "")[:800].replace("\n", " ")
        print(f"[{index + 1}/{total}] HTTP {resp.status_code} — {snippet}")
        return False
    try:
        data = resp.json()
    except json.JSONDecodeError:
        snippet = (resp.text or "")[:800].replace("\n", " ")
        print(
            f"[{index + 1}/{total}] INVALID JSON (backend error page?) — "
            f"check server logs. Body: {snippet}"
        )
        return False

    pressure = data.get("pressure_index", "?")
    risk = data.get("risk_level", "?")
    classification = data.get("classification", "?")
    alert = "[ALERT!]" if data.get("alert_triggered") else ""
    print(
        f"[{index + 1}/{total}] {loc:>10} | "
        f"Pressure: {pressure!s:>6} | "
        f"Risk: {risk!s:>8} | "
        f"{str(classification):>35} {alert}"
    )
    return True


def main():
    parser = argparse.ArgumentParser(description="Stream CSV data to Stampede Predictor API")
    parser.add_argument("--speed", type=float, default=2.0, help="Seconds between rows (default: 2)")
    parser.add_argument("--location", type=str, default=None, help="Filter to a specific location")
    parser.add_argument(
        "--scenario",
        type=str,
        default="live",
        choices=["live", "replay"],
        help="'live' for corridor CSV, 'replay' for replay_scenario.csv",
    )
    parser.add_argument("--max-rows", type=int, default=None, help="Maximum rows to stream")
    parser.add_argument("--api-url", type=str, default=None, help="Ingest URL (default: STAMPEDE_API_URL or :8080)")
    parser.add_argument(
        "--csv",
        type=str,
        default=None,
        help="Path to CSV for live scenario (default: data/corridor_readings_augmented.csv or STREAM_CSV)",
    )
    args = parser.parse_args()

    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(script_dir, ".."))

    if args.scenario == "replay":
        csv_path = os.path.join(project_root, "data", "replay_scenario.csv")
    else:
        csv_path = resolve_live_csv(project_root, args.csv)

    if not os.path.exists(csv_path):
        print(f"[ERROR] File not found: {csv_path}")
        print(
            "[ERROR] Run the pipeline first:\n"
            "  python scripts/integrate_pipeline.py\n"
            "Or set STREAM_CSV / use --csv to point at your augmented corridor file."
        )
        sys.exit(1)

    api_url = (args.api_url or default_api_url()).strip()

    print(f"[STREAM] Loading {csv_path}")
    df = pd.read_csv(csv_path)
    print(f"[STREAM] Loaded {len(df)} rows")

    if args.location:
        if "location" in df.columns:
            df = df[df["location"] == args.location]
            print(f"[STREAM] Filtered to {args.location}: {len(df)} rows")
        else:
            print(f"[STREAM] No 'location' column — will assign {args.location} to all rows")

    if args.max_rows:
        df = df.head(args.max_rows)
        print(f"[STREAM] Limited to {args.max_rows} rows")

    print(f"[STREAM] Speed: {args.speed}s between rows")
    print(f"[STREAM] Target: {api_url}")
    print("[STREAM] Starting in 2 seconds...")
    time.sleep(2)

    success_count = 0
    error_count = 0
    registered_events = {}

    for i, (_, row) in enumerate(df.iterrows()):
        raw_payload = row.to_dict()
        payload = {}
        for k, v in raw_payload.items():
            k_clean = str(k).lower().replace(" ", "_")
            payload[k_clean] = clean_value(v)
            payload[k] = clean_value(v)  # Preserve original casing for ML model
            
        payload = {k: v for k, v in payload.items() if v is not None}

        if "location" not in payload or pd.isna(payload.get("location")):
            if args.location:
                payload["location"] = args.location
            else:
                payload["location"] = DEFAULT_LOCATIONS[i % len(DEFAULT_LOCATIONS)]

        if "timestamp" in payload:
            payload["timestamp"] = str(payload["timestamp"])

        event_type = payload.pop("event_type", None)
        is_dynamic = bool(event_type and str(event_type).strip().lower() not in ["", "nan", "none", "temple"])

        if is_dynamic:
            vt_raw = str(event_type).lower()
            venue_type = "social"
            if "mela" in vt_raw: venue_type = "mela"
            elif "strike" in vt_raw or "disruption" in vt_raw: venue_type = "strike"
            elif "rally" in vt_raw: venue_type = "rally"
            elif "rath" in vt_raw or "procession" in vt_raw: venue_type = "procession"
            elif "stadium" in vt_raw or "arena" in vt_raw: venue_type = "stadium"
            
            loc_name = payload.get("location", "tbd")
            
            # The local key to know if we registered it locally in this session
            local_event_key = f"{venue_type}_{str(loc_name).lower()}"
            
            base_url = api_url.split("/api/")[0]
            
            if local_event_key not in registered_events:
                reg_payload = {
                    "name": f"{vt_raw.title().replace(' / Road Disruption', '')} · {str(loc_name).title()}",
                    "venue_type": venue_type,
                    "lat": 0, "lng": 0,
                    "radius_km": 1.0,
                    "form_factors": list(payload.keys())
                }
                try:
                    reg_resp = requests.post(f"{base_url}/api/events/register", json=reg_payload, timeout=5)
                    server_event_id = reg_resp.json()["location"]["id"]
                    registered_events[local_event_key] = server_event_id
                except Exception as e:
                    print(f"Failed to register event: {e}")
                    registered_events[local_event_key] = local_event_key # fallback
            
            server_event_id = registered_events.get(local_event_key, local_event_key)
            target_url = f"{base_url}/api/ingest/event/{server_event_id}"
            final_payload = {
                "timestamp": payload.get("timestamp"),
                "readings": payload
            }
        else:
            target_url = api_url
            final_payload = payload

        try:
            resp = requests.post(target_url, json=final_payload, timeout=30)
            loc = str(payload.get("location", "?"))
            if handle_ingest_response(resp, i, len(df), loc):
                success_count += 1
            else:
                error_count += 1
        except requests.exceptions.ConnectionError:
            print(f"[{i + 1}/{len(df)}] CONNECTION ERROR — is the backend running at {api_url}?")
            error_count += 1
            if error_count > 5:
                print("[STREAM] Too many connection errors. Stopping.")
                break
        except requests.exceptions.Timeout:
            print(f"[{i + 1}/{len(df)}] TIMEOUT — backend did not respond in time.")
            error_count += 1
        except Exception as e:
            print(f"[{i + 1}/{len(df)}] ERROR: {e}")
            error_count += 1

        time.sleep(args.speed)

    print(f"\n[STREAM] Done. {success_count} success, {error_count} errors.")


if __name__ == "__main__":
    main()
