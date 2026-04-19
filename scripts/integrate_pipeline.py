#!/usr/bin/env python3
"""
End-to-end data + ML pipeline (implements context.md §3 workflow).

  1) Run data_gen.py on a base corridor CSV → data/corridor_readings_augmented.csv (+ transit/toll/zone CSVs)
  2) Run backend/models/train_model.py → data/cleaned_dataset_augmented.csv + backend/models/saved_model.pkl

Environment:
  DATA_GEN_INPUT   Optional explicit path to base CSV (overrides auto-discovery).

Auto-discovery order for base CSV:
  1) DATA_GEN_INPUT
  2) data/corridor_readings.csv
  3) dataset/TS-PS11.csv
  4) First *.csv under dataset/

Usage (from repo root):
  python scripts/integrate_pipeline.py
  python scripts/integrate_pipeline.py --skip-augment   # only train (augmented CSV must exist)
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def find_base_csv() -> Path | None:
    env = os.environ.get("DATA_GEN_INPUT", "").strip()
    if env:
        p = Path(env)
        if p.is_file():
            return p.resolve()
        print(f"[WARN] DATA_GEN_INPUT set but not a file: {env}")

    candidates = [
        ROOT / "data" / "corridor_readings.csv",
        ROOT / "dataset" / "TS-PS11.csv",
    ]
    for c in candidates:
        if c.is_file():
            return c.resolve()

    dataset_dir = ROOT / "dataset"
    if dataset_dir.is_dir():
        csvs = sorted(dataset_dir.glob("*.csv"))
        if csvs:
            return csvs[0].resolve()
    return None


def main() -> int:
    parser = argparse.ArgumentParser(description="Augment corridor data then train ML models")
    parser.add_argument(
        "--skip-augment",
        action="store_true",
        help="Skip data_gen.py; train only (expects data/corridor_readings_augmented.csv)",
    )
    args = parser.parse_args()

    data_gen = ROOT / "data_gen.py"
    if not data_gen.is_file():
        print(f"[ERROR] Missing {data_gen}")
        return 1

    if not args.skip_augment:
        base = find_base_csv()
        if base is None:
            print(
                "[ERROR] No base corridor CSV found.\n"
                "  Set DATA_GEN_INPUT to your file, or add one of:\n"
                "    data/corridor_readings.csv\n"
                "    dataset/TS-PS11.csv\n"
                "    any dataset/*.csv"
            )
            return 1
        print(f"[PIPELINE] Step 1/2: data_gen.py --input {base}")
        r1 = subprocess.run(
            [
                sys.executable,
                str(data_gen),
                "--input",
                str(base),
                "--output_dir",
                str(ROOT / "data"),
            ],
            cwd=str(ROOT),
        )
        if r1.returncode != 0:
            print("[ERROR] data_gen.py failed")
            return r1.returncode
    else:
        print("[PIPELINE] Skipping augmentation (--skip-augment)")

    aug = ROOT / "data" / "corridor_readings_augmented.csv"
    if not aug.is_file():
        print(f"[ERROR] Augmented file missing after step 1: {aug}")
        return 1

    train = ROOT / "backend" / "models" / "train_model.py"
    if not train.is_file():
        print(f"[ERROR] Missing {train}")
        return 1

    print("[PIPELINE] Step 2/2: train_model.py")
    r2 = subprocess.run([sys.executable, str(train)], cwd=str(ROOT / "backend"))
    if r2.returncode != 0:
        print("[ERROR] train_model.py failed")
        return r2.returncode

    print("[PIPELINE] Done. Next: uvicorn + stream_data (see README.md).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
