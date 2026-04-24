# Stampede Window Predictor

A real-time crowd pressure intelligence system for pilgrimage corridors that predicts crush risks 8–12 minutes ahead and coordinates responses across agencies on a unified dashboard.

## Overview
This platform ingests raw crowd flow data, leverages machine learning models to predict crush risks, calculates a location-agnostic pressure index, and broadcasts real-time alerts via WebSocket to dynamic React dashboards tailored for coordinating Police, Temple Trust, and Transport authorities.

## Tech Stack
- **Frontend**: React, Vite, TailwindCSS (v4), Recharts, Leaflet
- **Backend**: Python, FastAPI, SQLite, WebSocket
- **ML & Data**: Scikit-learn (RandomForest), Pandas, Numpy

## Local Development & Demo Setup

### 1. Prerequisites
Ensure you have Node.js and Python 3.10+ installed.

### 2. Data augmentation + ML training (recommended)

The model expects **`data/corridor_readings_augmented.csv`**. Build it and train in one step from the repo root:

```bash
pip install -r backend/requirements.txt
python scripts/integrate_pipeline.py
```

This runs **`data_gen.py`** on a discovered base CSV (`data/corridor_readings.csv`, `dataset/TS-PS11.csv`, or `DATA_GEN_INPUT`) then **`backend/models/train_model.py`**, producing **`backend/models/saved_model.pkl`** and **`data/cleaned_dataset_augmented.csv`**.

Train only (if augmented CSV already exists):

```bash
cd backend
python models/train_model.py
# Optional overrides:
# python models/train_model.py --input ../data/corridor_readings_augmented.csv --output-cleaned ../data/cleaned_dataset_augmented.csv
```

Skip augmentation and only retrain:

```bash
python scripts/integrate_pipeline.py --skip-augment
```

### 3. Run the complete suite (Requires 3 terminals)

**Terminal 1 — Backend API**
Start the FastAPI backend with websocket broadcasting on port 8080.
```bash
cd backend
uvicorn main:app --reload --port 8080
```

**Terminal 2 — Frontend Application**
Start the React Vite dashboard.
```bash
cd frontend
npm install
npm run dev
# The dashboard will open typically at http://localhost:5173
```

**Terminal 3 — Live Data Simulation**
Feed the pre-processed data to the backend using the simulation engine. Defaults to **`http://localhost:8080/api/ingest`** (same port as Terminal 1). Override with **`STAMPEDE_API_URL`** or **`--api-url`** if needed.
```bash
cd simulation
python stream_data.py --speed 2
# Optional: custom CSV or API
# python stream_data.py --csv ../data/corridor_readings_augmented.csv --api-url http://localhost:8080/api/ingest
```

## Features Demonstrated

1. **Prediction Models**: Employs an RF regressor tuned to identify crush windows 8-12 mins into the future. 
2. **Unified Dashboard**: All coordinated authorities get a singular responsive view into identical data.
3. **Surge Classification**: Intelligent stateful classification distinguishing momentary surges from genuine crush buildups.
4. **Replay Mode**: Review scenarios in high-speed, highlighting precise points metrics breached critical bounds.
5. **Event Log Audit**: Fully searchable and exportable event audit trail covering trigger points and SLA resolutions.
