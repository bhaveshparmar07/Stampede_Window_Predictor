# Phase L & Phase M Changes Log

## Phase L Implementations
- **Skipped full Generation Run**: Validated that `data/` already contains `corridor_readings_augmented.csv` and `transit_simulation.csv` etc. We skipped running `data_gen.py` to prevent overwriting existing stable scenario outputs.
- **Created AI Services**: Added `backend/services/ai_triage.py` for Anthropic connection and initialized local memory logic in `backend/services/memory/static_memory.py` and `session_memory.py`.
- **Database Schema extensions**: Created `ai_triage_log` table and added missing multiplier columns to the `alerts` table. Made sure the sqlite3 operations ran smoothly without breaking existing data.

## Phase M Implementations
- **Location Registry**: Created `backend/services/location_registry.py` defining temples, stadiums, processions, and rallies. Exposes a dynamic registration list.
- **Form Factors**: Created `backend/services/form_factors.py` for generalized pressure algorithms per-entity type.
- **Correlation Engine**: Developed `backend/services/correlation_engine.py` to map external events mathematically into temple multipliers.
- **Base Backend Endpoints**: Added endpoints `/api/locations`, `/api/events/register`, and `/api/ingest/event/{event_id}`.
- **Unified Alert Multiplier Pipeline**: Updated `check` within the ingest loop in `main.py` so that Correlated Entity multipliers affect Temple pressures seamlessly.
- **Sidebar and Dashboard Reshaping**: `frontend/src/pages/Dashboard.jsx` now splits out "Dynamic Events" from permanent temples using the location API.
- **Component Swap Model**: Created `TempleCenterPanel.jsx` and `StadiumCenterPanel.jsx` so the central view intelligently swaps according to the selected `activeLocation` venue type.

