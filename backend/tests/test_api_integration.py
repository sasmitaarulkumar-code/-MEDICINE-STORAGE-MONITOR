from fastapi.testclient import TestClient
from app.main import app
from app.database import Base, engine

client = TestClient(app)

def test_health():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy", "service": "medguard-core-api"}

def test_storage_units_list():
    response = client.get("/api/v1/storage-units")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1

def test_telemetry_ingest_and_risk_eval():
    packet = {
        "storage_unit_code": "UNIT-A-FRIDGE",
        "temperature": 4.5,
        "humidity": 46.0,
        "light_lux": 15.0,
        "door_open": False,
        "power_connected": True,
        "battery_level": 3.3,
        "is_offline_sync": False
    }
    response = client.post("/api/v1/telemetry/ingest", json=packet)
    assert response.status_code == 201
    res_data = response.json()
    assert res_data["temperature"] == 4.5

def test_affected_inventory():
    response = client.get("/api/v1/inventory/affected/1")
    assert response.status_code == 200
    data = response.json()
    assert "storage_unit_code" in data
    assert "standard_operating_procedure" in data

def test_demo_scenario_trigger():
    req = {
        "scenario_id": 1,
        "unit_code": "UNIT-A-FRIDGE"
    }
    response = client.post("/api/v1/demo/trigger-scenario", json=req)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["status"] == "SAFE"

def test_storage_summary_report():
    response = client.get("/api/v1/reports/storage-summary?days=7")
    assert response.status_code == 200
    data = response.json()
    assert "units" in data
    assert len(data["units"]) >= 1
