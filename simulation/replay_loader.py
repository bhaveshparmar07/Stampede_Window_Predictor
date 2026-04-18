"""
Replay Loader — Loads replay_scenario.csv for the replay API endpoints.
"""

import os
import pandas as pd


def load_replay_frames(csv_path: str = None) -> list:
    """
    Load replay scenario CSV and return as list of dicts.
    
    Args:
        csv_path: Path to replay CSV. Defaults to data/replay_scenario.csv
    
    Returns:
        List of frame dictionaries.
    """
    if csv_path is None:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        csv_path = os.path.join(script_dir, "..", "data", "replay_scenario.csv")

    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"Replay scenario not found: {csv_path}")

    df = pd.read_csv(csv_path)
    return df.to_dict(orient="records")
