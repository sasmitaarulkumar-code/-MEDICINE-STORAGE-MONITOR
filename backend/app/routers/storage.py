from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.storage_unit import StorageUnit
from app.models.sensor_reading import SensorReading
from app.models.alert import Alert
from app.models.medicine import Medicine
from app.schemas.storage import StorageUnitCreate, StorageUnitUpdate, StorageUnitOut, StorageUnitSummary
from app.services.audit_service import AuditService

router = APIRouter(prefix="/storage-units", tags=["Storage Units"])

@router.get("", response_model=List[StorageUnitSummary])
def list_storage_units(db: Session = Depends(get_db)):
    units = db.query(StorageUnit).all()
    summaries = []
    
    for u in units:
        latest_reading = db.query(SensorReading).filter(
            SensorReading.storage_unit_id == u.id
        ).order_by(SensorReading.timestamp.desc()).first()

        active_alerts_count = db.query(Alert).filter(
            Alert.storage_unit_id == u.id,
            Alert.status.in_(["ACTIVE", "ACKNOWLEDGED"])
        ).count()

        med_count = db.query(Medicine).filter(Medicine.storage_unit_id == u.id).count()

        summaries.append(StorageUnitSummary(
            id=u.id,
            unit_code=u.unit_code,
            name=u.name,
            unit_type=u.unit_type,
            location=u.location,
            default_min_temp=u.default_min_temp,
            default_max_temp=u.default_max_temp,
            default_min_humidity=u.default_min_humidity,
            default_max_humidity=u.default_max_humidity,
            power_status=u.power_status,
            status=u.status,
            current_risk_score=u.current_risk_score,
            door_open_state=u.door_open_state,
            last_ping=u.last_ping,
            created_at=u.created_at,
            latest_temperature=latest_reading.temperature if latest_reading else None,
            latest_humidity=latest_reading.humidity if latest_reading else None,
            latest_light_lux=latest_reading.light_lux if latest_reading else None,
            active_alert_count=active_alerts_count,
            medicine_count=med_count
        ))
    return summaries

@router.post("", response_model=StorageUnitOut, status_code=status.HTTP_201_CREATED)
def create_storage_unit(unit_in: StorageUnitCreate, db: Session = Depends(get_db)):
    existing = db.query(StorageUnit).filter(StorageUnit.unit_code == unit_in.unit_code).first()
    if existing:
        raise HTTPException(status_code=400, detail="Storage unit with this code already exists")
    
    new_unit = StorageUnit(
        unit_code=unit_in.unit_code,
        name=unit_in.name,
        unit_type=unit_in.unit_type,
        location=unit_in.location,
        default_min_temp=unit_in.default_min_temp,
        default_max_temp=unit_in.default_max_temp,
        default_min_humidity=unit_in.default_min_humidity,
        default_max_humidity=unit_in.default_max_humidity
    )
    db.add(new_unit)
    db.commit()
    db.refresh(new_unit)
    AuditService.log_event(db, "STORAGE_UNIT_CREATED", "STORAGE_UNIT", new_unit.id, details={"code": new_unit.unit_code})
    return new_unit

@router.get("/{id}", response_model=StorageUnitOut)
def get_storage_unit(id: int, db: Session = Depends(get_db)):
    unit = db.query(StorageUnit).filter(StorageUnit.id == id).first()
    if not unit:
        raise HTTPException(status_code=404, detail="Storage unit not found")
    return unit

@router.put("/{id}", response_model=StorageUnitOut)
def update_storage_unit(id: int, update_in: StorageUnitUpdate, db: Session = Depends(get_db)):
    unit = db.query(StorageUnit).filter(StorageUnit.id == id).first()
    if not unit:
        raise HTTPException(status_code=404, detail="Storage unit not found")

    update_data = update_in.dict(exclude_unset=True)
    for field, val in update_data.items():
        setattr(unit, field, val)

    db.commit()
    db.refresh(unit)
    AuditService.log_event(db, "STORAGE_THRESHOLDS_UPDATED", "STORAGE_UNIT", unit.id, details=update_data)
    return unit
