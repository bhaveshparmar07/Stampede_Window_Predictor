-- Stampede Window Predictor — SQLite Schema

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

-- Alerts
CREATE TABLE IF NOT EXISTS alerts (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    triggered_at        TEXT NOT NULL,
    location            TEXT NOT NULL,
    pressure_index      REAL,
    risk_classification TEXT,
    crush_window_min    REAL,
    resolved_at         TEXT,
    status              TEXT DEFAULT 'active'
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
