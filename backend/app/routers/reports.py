import csv
import io
from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.models.storage_unit import StorageUnit
from app.models.sensor_reading import SensorReading
from app.models.alert import Alert
from app.models.audit import AuditLog

router = APIRouter(tags=["Reports & Compliance"])

@router.get("/reports/storage-summary")
def get_storage_summary_report(
    storage_unit_id: Optional[int] = None,
    days: int = 7,
    db: Session = Depends(get_db)
):
    cutoff = datetime.utcnow() - timedelta(days=days)
    
    query = db.query(StorageUnit)
    if storage_unit_id:
        query = query.filter(StorageUnit.id == storage_unit_id)
    units = query.all()

    reports = []
    for u in units:
        # Sensor stats
        readings_query = db.query(SensorReading).filter(
            SensorReading.storage_unit_id == u.id,
            SensorReading.timestamp >= cutoff
        )
        readings_count = readings_query.count()

        if readings_count > 0:
            avg_temp = db.query(func.avg(SensorReading.temperature)).filter(
                SensorReading.storage_unit_id == u.id,
                SensorReading.timestamp >= cutoff
            ).scalar() or 0.0

            max_temp = db.query(func.max(SensorReading.temperature)).filter(
                SensorReading.storage_unit_id == u.id,
                SensorReading.timestamp >= cutoff
            ).scalar() or 0.0

            min_temp = db.query(func.min(SensorReading.temperature)).filter(
                SensorReading.storage_unit_id == u.id,
                SensorReading.timestamp >= cutoff
            ).scalar() or 0.0

            avg_humid = db.query(func.avg(SensorReading.humidity)).filter(
                SensorReading.storage_unit_id == u.id,
                SensorReading.timestamp >= cutoff
            ).scalar() or 0.0

            door_open_events = readings_query.filter(SensorReading.door_open == True).count()
        else:
            avg_temp = max_temp = min_temp = avg_humid = 0.0
            door_open_events = 0

        # Alert statistics
        alerts = db.query(Alert).filter(
            Alert.storage_unit_id == u.id,
            Alert.triggered_at >= cutoff
        ).all()

        total_alerts = len(alerts)
        warning_alerts = sum(1 for a in alerts if a.alert_level == "WARNING")
        high_risk_alerts = sum(1 for a in alerts if a.alert_level == "HIGH_RISK")
        critical_alerts = sum(1 for a in alerts if a.alert_level == "CRITICAL")
        total_deviation_sec = sum(a.duration_seconds for a in alerts)

        reports.append({
            "storage_unit_id": u.id,
            "unit_code": u.unit_code,
            "unit_name": u.name,
            "unit_type": u.unit_type,
            "location": u.location,
            "monitoring_period_days": days,
            "readings_collected": readings_count,
            "temperature_stats": {
                "average_c": round(avg_temp, 1),
                "maximum_c": round(max_temp, 1),
                "minimum_c": round(min_temp, 1),
                "configured_min_c": u.default_min_temp,
                "configured_max_c": u.default_max_temp
            },
            "humidity_stats": {
                "average_percent": round(avg_humid, 1),
                "configured_max_percent": u.default_max_humidity
            },
            "incident_and_alert_metrics": {
                "total_alerts": total_alerts,
                "warning_level": warning_alerts,
                "high_risk_level": high_risk_alerts,
                "critical_level": critical_alerts,
                "total_deviation_duration_minutes": round(total_deviation_sec / 60.0, 1),
                "door_open_samples": door_open_events
            },
            "compliance_status": "COMPLIANT" if critical_alerts == 0 and high_risk_alerts == 0 else "AUDIT_REQUIRED"
        })

    return {
        "generated_at": datetime.utcnow().isoformat(),
        "report_type": "MEDGUARD Quality & Cold-Chain Compliance Audit",
        "units": reports
    }

@router.get("/reports/export-csv")
def export_telemetry_csv(
    storage_unit_id: int,
    days: int = 3,
    db: Session = Depends(get_db)
):
    unit = db.query(StorageUnit).filter(StorageUnit.id == storage_unit_id).first()
    if not unit:
        raise HTTPException(status_code=404, detail="Storage unit not found")

    cutoff = datetime.utcnow() - timedelta(days=days)
    readings = db.query(SensorReading).filter(
        SensorReading.storage_unit_id == unit.id,
        SensorReading.timestamp >= cutoff
    ).order_by(SensorReading.timestamp.asc()).all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Timestamp (UTC)", "Storage Unit", "Temperature (C)", "Humidity (%)",
        "Light (Lux)", "Door Opened", "Power Connected", "Battery (V)", "Is Offline Sync"
    ])

    for r in readings:
        writer.writerow([
            r.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            unit.unit_code,
            r.temperature,
            r.humidity,
            r.light_lux,
            "YES" if r.door_open else "NO",
            "ON" if r.power_connected else "OFF",
            r.battery_level,
            "YES" if r.is_offline_sync else "NO"
        ])

    return Response(
        content=output.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=medguard_{unit.unit_code}_report.csv"}
    )

@router.get("/audit/logs")
def get_audit_logs(limit: int = 50, db: Session = Depends(get_db)):
    logs = db.query(AuditLog).order_by(AuditLog.timestamp.desc()).limit(limit).all()
    return [
        {
            "id": l.id,
            "action": l.action,
            "entity_type": l.entity_type,
            "entity_id": l.entity_id,
            "user_name": l.user.full_name if l.user else "System Automation",
            "ip_address": l.ip_address,
            "details": l.details_json,
            "timestamp": l.timestamp.isoformat()
        }
        for l in logs
    ]
