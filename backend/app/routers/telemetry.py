from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Header, status
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models.storage_unit import StorageUnit
from app.models.sensor_reading import SensorReading
from app.models.alert import Alert
from app.schemas.telemetry import TelemetryIngest, TelemetrySyncBatch, SensorReadingOut
from app.services.risk_engine import RiskScoreEngine
from app.services.trend_forecaster import TrendForecaster
from app.services.anomaly_detector import AnomalyDetector
from app.services.alert_manager import AlertManager
from app.services.audit_service import AuditService
from app.websocket_manager import ws_manager

router = APIRouter(prefix="/telemetry", tags=["Telemetry"])

@router.post("/ingest", response_model=SensorReadingOut, status_code=status.HTTP_201_CREATED)
async def ingest_telemetry(
    data: TelemetryIngest,
    x_device_key: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    # Device authentication check (relaxed in dev/demo mode)
    if x_device_key and x_device_key != settings.DEVICE_API_KEY:
        raise HTTPException(status_code=401, detail="Invalid Device API Key")

    # Locate storage unit
    unit = db.query(StorageUnit).filter(StorageUnit.unit_code == data.storage_unit_code).first()
    if not unit:
        # Auto-provision unit if unknown code encountered
        unit = StorageUnit(
            unit_code=data.storage_unit_code,
            name=f"Storage Unit {data.storage_unit_code}",
            unit_type="refrigerator",
            location="Ward Storage Area"
        )
        db.add(unit)
        db.commit()
        db.refresh(unit)

    # 1. Record Telemetry Snapshot
    now = data.timestamp or datetime.utcnow()
    reading = SensorReading(
        storage_unit_id=unit.id,
        temperature=data.temperature,
        humidity=data.humidity,
        light_lux=data.light_lux,
        door_open=data.door_open,
        power_connected=data.power_connected,
        battery_level=data.battery_level,
        is_offline_sync=data.is_offline_sync,
        timestamp=now
    )
    db.add(reading)
    db.commit()
    db.refresh(reading)

    # 2. Fetch recent window for analytics (last 20 readings)
    past_readings = db.query(SensorReading).filter(
        SensorReading.storage_unit_id == unit.id
    ).order_by(SensorReading.timestamp.desc()).limit(25).all()
    past_readings.reverse() # chronological order

    # Format for trend forecaster
    time_temp_series = [(r.timestamp.timestamp(), r.temperature) for r in past_readings]
    trend_result = TrendForecaster.analyze_trend(
        time_temp_series,
        target_max_temp=unit.default_max_temp,
        target_min_temp=unit.default_min_temp
    )

    # Anomaly detection on temperature
    recent_temps = [r.temperature for r in past_readings]
    anomaly_result = AnomalyDetector.detect_anomalies(
        recent_values=recent_temps[:-1] if len(recent_temps) > 1 else recent_temps,
        current_value=data.temperature,
        metric_name="Temperature"
    )

    # Calculate door open duration
    door_open_seconds = 0
    if data.door_open:
        # count consecutive door open readings
        open_count = 0
        for r in reversed(past_readings):
            if r.door_open:
                open_count += 1
            else:
                break
        door_open_seconds = open_count * 5  # assuming ~5s interval

    # Recent 24h alert count
    recent_alerts_count = db.query(Alert).filter(
        Alert.storage_unit_id == unit.id,
        Alert.triggered_at >= now - timedelta(hours=24)
    ).count()

    # 3. Calculate 0-100 Risk Score
    risk_eval = RiskScoreEngine.calculate_score(
        temperature=data.temperature,
        humidity=data.humidity,
        door_open=data.door_open,
        door_open_seconds=door_open_seconds,
        power_connected=data.power_connected,
        light_lux=data.light_lux,
        min_temp=unit.default_min_temp,
        max_temp=unit.default_max_temp,
        min_humid=unit.default_min_humidity,
        max_humid=unit.default_max_humidity,
        recent_alert_count_24h=recent_alerts_count
    )

    # 4. Update Storage Unit state
    unit.current_risk_score = risk_eval["risk_score"]
    unit.status = risk_eval["status"]
    unit.power_status = data.power_connected
    unit.door_open_state = data.door_open
    unit.last_ping = now
    db.commit()

    # 5. Process Multi-level Alerts
    alerts = AlertManager.process_telemetry_alerts(
        db=db,
        unit=unit,
        reading=reading,
        trend_result=trend_result,
        anomaly_result=anomaly_result,
        risk_result=risk_eval
    )

    # 6. Broadcast live packet over WebSockets
    live_payload = {
        "event_type": "TELEMETRY_UPDATE",
        "storage_unit_id": unit.id,
        "storage_unit_code": unit.unit_code,
        "storage_unit_name": unit.name,
        "temperature": data.temperature,
        "humidity": data.humidity,
        "light_lux": data.light_lux,
        "door_open": data.door_open,
        "power_connected": data.power_connected,
        "battery_level": data.battery_level,
        "risk_score": risk_eval["risk_score"],
        "status": risk_eval["status"],
        "risk_breakdown": risk_eval["breakdown"],
        "trend": trend_result,
        "anomaly": anomaly_result,
        "new_alerts_count": len(alerts),
        "timestamp": now.isoformat()
    }
    await ws_manager.broadcast(live_payload)

    return reading

@router.post("/sync", status_code=status.HTTP_201_CREATED)
async def sync_offline_telemetry(
    batch: TelemetrySyncBatch,
    db: Session = Depends(get_db)
):
    unit = db.query(StorageUnit).filter(StorageUnit.unit_code == batch.storage_unit_code).first()
    if not unit:
        raise HTTPException(status_code=404, detail="Storage unit not found for sync")

    now = datetime.utcnow()
    created_count = 0

    for item in batch.readings:
        # Calculate timestamp based on offset or fallback
        ts = item.timestamp
        if not ts and item.timestamp_offset_s is not None:
            ts = now - timedelta(seconds=max(0, 300 - item.timestamp_offset_s))
        else:
            ts = now

        reading = SensorReading(
            storage_unit_id=unit.id,
            temperature=item.temperature,
            humidity=item.humidity,
            light_lux=item.light_lux,
            door_open=item.door_open,
            power_connected=item.power_connected,
            battery_level=item.battery_level,
            is_offline_sync=True,
            timestamp=ts
        )
        db.add(reading)
        created_count += 1

    db.commit()
    AuditService.log_event(
        db=db,
        action="OFFLINE_TELEMETRY_SYNCED",
        entity_type="STORAGE_UNIT",
        entity_id=unit.id,
        details={"record_count": created_count, "unit": unit.unit_code}
    )

    # Broadcast sync notification
    await ws_manager.broadcast({
        "event_type": "OFFLINE_SYNC_COMPLETED",
        "storage_unit_id": unit.id,
        "unit_code": unit.unit_code,
        "synced_records": created_count,
        "timestamp": now.isoformat()
    })

    return {"message": f"Successfully synchronized {created_count} offline records", "unit_code": unit.unit_code}

@router.get("/history/{unit_id}", response_model=List[SensorReadingOut])
def get_telemetry_history(
    unit_id: int,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    readings = db.query(SensorReading).filter(
        SensorReading.storage_unit_id == unit_id
    ).order_by(SensorReading.timestamp.desc()).limit(limit).all()
    readings.reverse()
    return readings
