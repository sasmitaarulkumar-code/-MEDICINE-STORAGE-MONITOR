from datetime import datetime, timedelta
from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.storage_unit import StorageUnit
from app.models.alert import Alert
from app.models.sensor_reading import SensorReading
from app.services.audit_service import AuditService

class AlertManager:
    """
    Evaluates sensor readings, manages multi-level alert lifecycle,
    and prevents duplicate alert storms.
    """

    @staticmethod
    def process_telemetry_alerts(
        db: Session,
        unit: StorageUnit,
        reading: SensorReading,
        trend_result: dict,
        anomaly_result: dict,
        risk_result: dict
    ) -> List[Alert]:
        generated_alerts = []
        now = datetime.utcnow()

        # 1. Power Interruption Alert
        if not reading.power_connected:
            existing_power = db.query(Alert).filter(
                Alert.storage_unit_id == unit.id,
                Alert.alert_type == "POWER_FAIL",
                Alert.status == "ACTIVE"
            ).first()
            if not existing_power:
                alert = Alert(
                    storage_unit_id=unit.id,
                    alert_level="CRITICAL",
                    alert_type="POWER_FAIL",
                    trigger_value=0.0,
                    status="ACTIVE",
                    description=f"POWER INTERRUPTION DETECTED on {unit.name}. Unit operating on reserve power.",
                    recommended_action="Inspect facility breaker and verify emergency backup generator status immediately.",
                    triggered_at=now
                )
                db.add(alert)
                db.commit()
                db.refresh(alert)
                generated_alerts.append(alert)
                AuditService.log_event(db, "POWER_INTERRUPTION_ALERT", "ALERT", alert.id, details={"unit": unit.unit_code})
        else:
            # Auto-resolve power alert if power restored
            active_power = db.query(Alert).filter(
                Alert.storage_unit_id == unit.id,
                Alert.alert_type == "POWER_FAIL",
                Alert.status == "ACTIVE"
            ).first()
            if active_power:
                active_power.status = "RESOLVED"
                active_power.resolved_at = now
                db.commit()
                AuditService.log_event(db, "POWER_RESTORED", "ALERT", active_power.id, details={"unit": unit.unit_code})

        # 2. Temperature Threshold Violation
        temp = reading.temperature
        min_t = unit.default_min_temp
        max_t = unit.default_max_temp

        if temp > max_t:
            deviation = temp - max_t
            level = "CRITICAL" if deviation >= 4.0 else ("HIGH_RISK" if deviation >= 1.5 else "WARNING")
            
            existing_temp_high = db.query(Alert).filter(
                Alert.storage_unit_id == unit.id,
                Alert.alert_type == "TEMP_HIGH",
                Alert.status.in_(["ACTIVE", "ACKNOWLEDGED"])
            ).first()

            if not existing_temp_high:
                alert = Alert(
                    storage_unit_id=unit.id,
                    alert_level=level,
                    alert_type="TEMP_HIGH",
                    trigger_value=temp,
                    allowed_range_min=min_t,
                    allowed_range_max=max_t,
                    status="ACTIVE",
                    description=f"Storage temperature ({temp:.1f}°C) exceeded configured upper limit of {max_t:.1f}°C.",
                    recommended_action="Verify door seal, inspect compressor coils, and review impacted medicine inventory.",
                    triggered_at=now
                )
                db.add(alert)
                db.commit()
                db.refresh(alert)
                generated_alerts.append(alert)
                AuditService.log_event(db, "TEMP_HIGH_ALERT_CREATED", "ALERT", alert.id, details={"temp": temp, "limit": max_t})
            else:
                # Update duration on existing alert
                delta_s = int((now - existing_temp_high.triggered_at).total_seconds())
                existing_temp_high.duration_seconds = delta_s
                if level == "CRITICAL" and existing_temp_high.alert_level != "CRITICAL":
                    existing_temp_high.alert_level = "CRITICAL"
                db.commit()

        elif temp < min_t:
            deviation = min_t - temp
            level = "CRITICAL" if deviation >= 3.0 else ("HIGH_RISK" if deviation >= 1.0 else "WARNING")

            existing_temp_low = db.query(Alert).filter(
                Alert.storage_unit_id == unit.id,
                Alert.alert_type == "TEMP_LOW",
                Alert.status.in_(["ACTIVE", "ACKNOWLEDGED"])
            ).first()

            if not existing_temp_low:
                alert = Alert(
                    storage_unit_id=unit.id,
                    alert_level=level,
                    alert_type="TEMP_LOW",
                    trigger_value=temp,
                    allowed_range_min=min_t,
                    allowed_range_max=max_t,
                    status="ACTIVE",
                    description=f"Storage temperature ({temp:.1f}°C) dropped below minimum safe limit of {min_t:.1f}°C.",
                    recommended_action="Risk of freezing sensitive biologics/vaccines! Check thermostat calibration.",
                    triggered_at=now
                )
                db.add(alert)
                db.commit()
                db.refresh(alert)
                generated_alerts.append(alert)
                AuditService.log_event(db, "TEMP_LOW_ALERT_CREATED", "ALERT", alert.id, details={"temp": temp, "limit": min_t})

        else:
            # Temperature normal: if existing active alert was present, auto-resolve after safe period
            active_temp_alerts = db.query(Alert).filter(
                Alert.storage_unit_id == unit.id,
                Alert.alert_type.in_(["TEMP_HIGH", "TEMP_LOW"]),
                Alert.status == "ACTIVE"
            ).all()
            for al in active_temp_alerts:
                al.status = "RESOLVED"
                al.resolved_at = now
                AuditService.log_event(db, "TEMP_ALERT_AUTO_RESOLVED", "ALERT", al.id, details={"temp": temp})
            if active_temp_alerts:
                db.commit()

        # 3. Door Ajar Alert
        if reading.door_open:
            existing_door = db.query(Alert).filter(
                Alert.storage_unit_id == unit.id,
                Alert.alert_type == "DOOR_AJAR",
                Alert.status.in_(["ACTIVE", "ACKNOWLEDGED"])
            ).first()

            if not existing_door:
                alert = Alert(
                    storage_unit_id=unit.id,
                    alert_level="WARNING",
                    alert_type="DOOR_AJAR",
                    trigger_value=1.0,
                    status="ACTIVE",
                    description=f"Storage unit door opened on {unit.name}.",
                    recommended_action="Ensure cabinet door is securely latched to prevent cold air leakage.",
                    triggered_at=now
                )
                db.add(alert)
                db.commit()
                db.refresh(alert)
                generated_alerts.append(alert)
            else:
                delta_s = int((now - existing_door.triggered_at).total_seconds())
                existing_door.duration_seconds = delta_s
                if delta_s >= 180 and existing_door.alert_level != "CRITICAL":
                    existing_door.alert_level = "CRITICAL"
                    existing_door.description = f"Storage unit door left open for {delta_s // 60} minutes! Thermal loss in progress."
                db.commit()
        else:
            active_door = db.query(Alert).filter(
                Alert.storage_unit_id == unit.id,
                Alert.alert_type == "DOOR_AJAR",
                Alert.status == "ACTIVE"
            ).first()
            if active_door:
                active_door.status = "RESOLVED"
                active_door.resolved_at = now
                db.commit()

        # 4. Early Warning Trend Alert
        if trend_result.get("has_warning"):
            existing_trend = db.query(Alert).filter(
                Alert.storage_unit_id == unit.id,
                Alert.alert_type == "TREND_WARNING",
                Alert.status == "ACTIVE"
            ).first()
            if not existing_trend:
                alert = Alert(
                    storage_unit_id=unit.id,
                    alert_level="WARNING",
                    alert_type="TREND_WARNING",
                    trigger_value=trend_result["slope_c_per_min"],
                    status="ACTIVE",
                    description=trend_result["description"],
                    recommended_action="Potential cooling system failure detected before threshold breach. Inspect airflow and seals.",
                    triggered_at=now
                )
                db.add(alert)
                db.commit()
                db.refresh(alert)
                generated_alerts.append(alert)

        # 5. Statistical Anomaly Alert
        if anomaly_result.get("is_anomaly"):
            alert = Alert(
                storage_unit_id=unit.id,
                alert_level="WARNING",
                alert_type="ANOMALY_SPIKE",
                trigger_value=anomaly_result["z_score"],
                status="ACTIVE",
                description=anomaly_result["details"],
                recommended_action="Review sensor placement and wiring to rule out electrical noise or thermal shock.",
                triggered_at=now
            )
            db.add(alert)
            db.commit()
            db.refresh(alert)
            generated_alerts.append(alert)

        return generated_alerts
