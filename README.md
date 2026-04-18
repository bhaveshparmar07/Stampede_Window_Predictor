# Stampede Window Predictor — Lakshya 2.0 (TS-11)

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

### 2. Setup and ML Training
First, train the machine learning models and clean the data. This will output a `saved_model.pkl` in the `backend/models/` folder and generate the cleaned datasets for simulation.
```bash
cd backend
pip install -r requirements.txt
python models/train_model.py
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
Feed the pre-processed data to the backend using the simulation engine. This auto routes the events based on the timestamps in the database to mimic real-world tracking.
```bash
cd simulation
python stream_data.py --speed 2
```

## Features Demonstrated

1. **Prediction Models**: Employs an RF regressor tuned to identify crush windows 8-12 mins into the future. 
2. **Unified Dashboard**: All coordinated authorities get a singular responsive view into identical data.
3. **Surge Classification**: Intelligent stateful classification distinguishing momentary surges from genuine crush buildups.
4. **Replay Mode**: Review scenarios in high-speed, highlighting precise points metrics breached critical bounds.
5. **Event Log Audit**: Fully searchable and exportable event audit trail covering trigger points and SLA resolutions.