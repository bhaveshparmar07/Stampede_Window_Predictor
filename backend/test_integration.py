from fastapi.testclient import TestClient
from main import app
import time

client = TestClient(app)

def test_health():
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ok"
    assert "model_loaded" in data

def test_ingest_and_alert():
    # Send a normal low-pressure payload
    res = client.post("/api/ingest", json={
        "location": "TestLocationSafe",
        "entry_flow_rate_pax_per_min": 10,
        "exit_flow_rate_pax_per_min": 20,
        "corridor_width_m": 5,
        "queue_density_pax_per_m2": 1,
        "transport_arrival_burst": 0
    })
    
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ok"
    assert data["location"] == "TestLocationSafe"
    assert "pressure_index" in data
    assert data["alert_triggered"] is False

    # Force a massive pressure spike payload to trigger an alarm
    # We will send 5 high readings sequentially to bypass the surge filter
    for _ in range(5):
        res2 = client.post("/api/ingest", json={
            "location": "TestLocationSpike",
            "entry_flow_rate_pax_per_min": 500,
            "exit_flow_rate_pax_per_min": 0,
            "corridor_width_m": 2,
            "queue_density_pax_per_m2": 8,
            "transport_arrival_burst": 200,
            "festival_peak": 1
        })
        assert res2.status_code == 200

    data = res2.json()
    assert data["status"] == "ok"
    assert data["classification"] == "GENUINE CRUSH BUILDUP" 
    # An alert should have triggered since pressure >= 70 and classification is Genuine
    # Though there's a chance it might fail if ML models predict 'Low' and override?
    # Actually, alert trigger logic doesn't depend on ML classifier directly, just the manual override logic in crush_classifier.py
    
    assert data["pressure_index"] > 70
    assert data["alert_triggered"] is True

def test_events_log():
    res = client.get("/api/events?limit=5")
    assert res.status_code == 200
    data = res.json()
    assert "events" in data
    assert "total" in data
    assert isinstance(data["events"], list)
    
def test_replay_endpoints():
    # Test reset
    res1 = client.post("/api/replay/reset")
    assert res1.status_code == 200
    
    # Test frame load without start (should fail or return error message)
    res2 = client.get("/api/replay/frame")
    assert res2.status_code == 200
    data2 = res2.json()
    assert "error" in data2["status"]
    
    # Now start replay
    res3 = client.post("/api/replay/start")
    assert res3.status_code == 200
    
    # Now get frame
    res4 = client.get("/api/replay/frame")
    assert res4.status_code == 200
    assert res4.json()["status"] == "ok"
