-- Stampede Window Predictor — SQLite Schema (v2 — with scenario extensions)

-- Pressure readings log
CREATE TABLE IF NOT EXISTS pressure_readings (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp           TEXT NOT NULL,
    location            TEXT NOT NULL,
    pressure_index      REAL,
    entry_flow          REAL,
    exit_flow           REAL,
    transport_burst     REAL,
    queue_density       REAL,
    risk_level          TEXT,
    crush_window_min    REAL
);

-- Alerts (extended with anomaly + scenario columns)
CREATE TABLE IF NOT EXISTS alerts (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    triggered_at        TEXT NOT NULL,
    location            TEXT NOT NULL,
    pressure_index      REAL,
    risk_classification TEXT,
    crush_window_min    REAL,
    resolved_at         TEXT,
    status              TEXT DEFAULT 'active',
    alert_type          TEXT DEFAULT 'crush_alert',
    anomaly_z_score     REAL,
    anomaly_severity    TEXT,
    scenario            TEXT
);

-- Agency acknowledgements
CREATE TABLE IF NOT EXISTS acknowledgements (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    alert_id            INTEGER NOT NULL,
    agency              TEXT NOT NULL,
    acknowledged_at     TEXT NOT NULL,
    response_time_sec   INTEGER,
    action_taken        TEXT,
    FOREIGN KEY (alert_id) REFERENCES alerts(id)
);

-- Event archive
CREATE TABLE IF NOT EXISTS event_log (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    event_type          TEXT,
    location            TEXT,
    timestamp           TEXT NOT NULL,
    details             TEXT
);

-- S3: Transit readings
CREATE TABLE IF NOT EXISTS transit_readings (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp           TEXT NOT NULL,
    segment_id          TEXT,
    bus_id              TEXT,
    vehicles_in_transit INTEGER,
    avg_occupancy       INTEGER,
    eta_to_choke_min    REAL,
    target_corridor     TEXT,
    projected_pressure  REAL
);

-- S4: Toll booth readings
CREATE TABLE IF NOT EXISTS toll_readings (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp           TEXT NOT NULL,
    booth_id            TEXT NOT NULL,
    vehicles_per_min    REAL,
    surge_ratio         REAL,
    target_corridor     TEXT,
    alert_tier          TEXT
);

-- S5: Zone readings
CREATE TABLE IF NOT EXISTS zone_readings (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp           TEXT NOT NULL,
    zone_id             TEXT NOT NULL,
    zone_type           TEXT,
    location            TEXT,
    utilization_pct     REAL,
    pax_count           INTEGER,
    capacity            INTEGER,
    buffer_penalty      REAL
);

-- S1: Scheduled events
CREATE TABLE IF NOT EXISTS scheduled_events (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id            TEXT UNIQUE,
    event_type          TEXT,
    venue               TEXT,
    start_time          TEXT,
    expected_attendance INTEGER,
    nearby_corridors    TEXT,
    distance_km         REAL,
    status              TEXT DEFAULT 'scheduled'
);
