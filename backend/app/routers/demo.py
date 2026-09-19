from datetime import datetime, timedelta
from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.database import get_db
from app.models.storage_unit import StorageUnit
from app.models.sensor_reading import SensorReading
from app.models.alert import Alert
from app.services.risk_engine import RiskScoreEngine
from app.services.alert_manager import AlertManager
from app.services.audit_service import AuditService
from app.websocket_manager import ws_manager

router = APIRouter(prefix="/demo", tags=["Hackathon Demo Controller"])

class DemoScenarioRequest(BaseModel):
    scenario_id: int  # 1 to 6
    unit_code: str = "UNIT-A-FRIDGE"

@router.post("/trigger-scenario")
async def trigger_demo_scenario(
    req: DemoScenarioRequest,
    db: Session = Depends(get_db)
):
    unit = db.query(StorageUnit).filter(StorageUnit.unit_code == req.unit_code).first()
    if not unit:
        raise HTTPException(status_code=404, detail="Storage unit not found for demo")

    now = datetime.utcnow()
    scenario_names = {
        1: "Scenario 1: Normal Safe Baseline",
        2: "Scenario 2: Early Warning Continuous Warming Trend",
        3: "Scenario 3: Critical Threshold Breach (>10°C) with Affected Inventory",
        4: "Scenario 4: Prolonged Door Ajar (>3 minutes)",
        5: "Scenario 5: Power Failure / Interruption Event",
        6: "Scenario 6: Recovery & Resolution Workflow"
    }

    if req.scenario_id not in scenario_names:
        raise HTTPException(status_code=400, detail="Invalid scenario_id (1-6)")

    # 1. Clear or adjust based on scenario
    if req.scenario_id == 1:
        # Normal baseline
        temp = 4.2
        humid = 48.0
        lux = 12.0
        door = False
        pwr = True
        desc = "Storage conditions nominal. All parameters within safe limits."

    elif req.scenario_id == 2:
        # Trend warning: seed previous 5 readings rising fast
        base_t = 5.2
        for i in range(5):
            past_time = now - timedelta(seconds=(5 - i) * 60)
            sample_temp = round(base_t + i * 0.45, 1)
            sr = SensorReading(
                storage_unit_id=unit.id,
                temperature=sample_temp,
                humidity=52.0,
                light_lux=15.0,
                door_open=False,
                power_connected=True,
                timestamp=past_time
            )
            db.add(sr)
        temp = 7.4
        humid = 53.0
        lux = 15.0
        door = False
        pwr = True
        desc = "Continuous warming detected (+0.45°C/min). Approaching 8.0°C upper limit."

    elif req.scenario_id == 3:
        # Critical threshold breach
        temp = 10.6
        humid = 68.5
        lux = 25.0
        door = False
        pwr = True
        desc = "Critical thermal excursion! Temperature (10.6°C) exceeds upper limit (8.0°C)."

    elif req.scenario_id == 4:
        # Door open event
        temp = 8.5
        humid = 72.0
        lux = 480.0
        door = True
        pwr = True
        desc = "Refrigerator door left open for over 3 minutes. High light and humidity intrusion."

    elif req.scenario_id == 5:
        # Power failure
        temp = 9.2
        humid = 62.0
        lux = 0.0
        door = False
        pwr = False
        desc = "POWER INTERRUPTION DETECTED: Primary AC mains offline. Operating on backup."

    elif req.scenario_id == 6:
        # Recovery
        temp = 4.4
        humid = 49.0
        lux = 10.0
        door = False
        pwr = True
        desc = "Environmental parameters recovered to normal 4.4°C. Ready for operator confirmation."

    # Save the current reading
    reading = SensorReading(
        storage_unit_id=unit.id,
        temperature=temp,
        humidity=humid,
        light_lux=lux,
        door_open=door,
        power_connected=pwr,
        battery_level=3.3 if pwr else 2.6,
        is_offline_sync=False,
        timestamp=now
    )
    db.add(reading)
    db.commit()
    db.refresh(reading)

    # Calculate door seconds
    door_secs = 210 if door else 0

    # Risk evaluation
    risk_eval = RiskScoreEngine.calculate_score(
        temperature=temp,
        humidity=humid,
        door_open=door,
        door_open_seconds=door_secs,
        power_connected=pwr,
        light_lux=lux,
        min_temp=unit.default_min_temp,
        max_temp=unit.default_max_temp,
        min_humid=unit.default_min_humidity,
        max_humid=unit.default_max_humidity,
        recent_alert_count_24h=1 if req.scenario_id in [3, 4, 5] else 0
    )

    unit.current_risk_score = risk_eval["risk_score"]
    unit.status = risk_eval["status"]
    unit.power_status = pwr
    unit.door_open_state = door
    unit.last_ping = now
    db.commit()

    # Generate or auto-resolve alerts
    trend_data = {
        "has_warning": (req.scenario_id == 2),
        "slope_c_per_min": 0.45 if req.scenario_id == 2 else 0.02,
        "trend_direction": "WARMING" if req.scenario_id == 2 else "STABLE",
        "estimated_time_to_breach_min": 1.3 if req.scenario_id == 2 else None,
        "confidence_percent": 94.0 if req.scenario_id == 2 else 10.0,
        "description": "Continuous warming trend detected (+0.45°C/min). Estimated breach in 1.3 minutes." if req.scenario_id == 2 else "Stable"
    }

    anomaly_data = {
        "is_anomaly": (req.scenario_id == 3),
        "z_score": 3.4 if req.scenario_id == 3 else 0.4,
        "details": "Rapid thermal drift detected (+5.4°C elevation)." if req.scenario_id == 3 else "Normal"
    }

    alerts = AlertManager.process_telemetry_alerts(
        db=db,
        unit=unit,
        reading=reading,
        trend_result=trend_data,
        anomaly_result=anomaly_data,
        risk_result=risk_eval
    )

    AuditService.log_event(
        db, "DEMO_SCENARIO_TRIGGERED", "STORAGE_UNIT", unit.id,
        details={"scenario_id": req.scenario_id, "scenario": scenario_names[req.scenario_id]}
    )

    # Broadcast over WebSocket
    await ws_manager.broadcast({
        "event_type": "DEMO_SCENARIO_APPLIED",
        "scenario_id": req.scenario_id,
        "scenario_name": scenario_names[req.scenario_id],
        "storage_unit_id": unit.id,
        "storage_unit_code": unit.unit_code,
        "temperature": temp,
        "humidity": humid,
        "light_lux": lux,
        "door_open": door,
        "power_connected": pwr,
        "risk_score": risk_eval["risk_score"],
        "status": risk_eval["status"],
        "trend": trend_data,
        "anomaly": anomaly_data,
        "timestamp": now.isoformat()
    })

    return {
        "success": True,
        "scenario_id": req.scenario_id,
        "scenario_name": scenario_names[req.scenario_id],
        "applied_temperature": temp,
        "applied_humidity": humid,
        "status": risk_eval["status"],
        "risk_score": risk_eval["risk_score"],
        "alerts_generated": len(alerts)
    }

@router.post("/reset")
async def reset_demo(db: Session = Depends(get_db)):
    # Auto-resolve all active alerts
    db.query(Alert).filter(Alert.status == "ACTIVE").update({
        "status": "RESOLVED",
        "resolved_at": datetime.utcnow()
    })
    # Reset storage units to safe state
    units = db.query(StorageUnit).all()
    for u in units:
        u.status = "SAFE"
        u.current_risk_score = 10.0
        u.power_status = True
        u.door_open_state = False
        u.last_ping = datetime.utcnow()
    db.commit()

    await ws_manager.broadcast({
        "event_type": "DEMO_RESET",
        "message": "System reset to normal baseline state",
        "timestamp": datetime.utcnow().isoformat()
    })
    return {"message": "Demo state reset to normal safe baseline."}
