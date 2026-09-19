from datetime import datetime, date
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.medicine import Medicine, MedicineBatch
from app.models.storage_unit import StorageUnit
from app.models.sensor_reading import SensorReading
from app.schemas.medicine import MedicineCreate, MedicineOut, AffectedInventoryReport, AffectedBatchItem
from app.services.audit_service import AuditService

router = APIRouter(prefix="", tags=["Medicines & Inventory"])

@router.get("/medicines", response_model=List[MedicineOut])
def list_medicines(storage_unit_id: Optional[int] = None, db: Session = Depends(get_db)):
    query = db.query(Medicine)
    if storage_unit_id:
        query = query.filter(Medicine.storage_unit_id == storage_unit_id)
    return query.all()

@router.post("/medicines", response_model=MedicineOut, status_code=status.HTTP_201_CREATED)
def create_medicine(med_in: MedicineCreate, db: Session = Depends(get_db)):
    unit = db.query(StorageUnit).filter(StorageUnit.id == med_in.storage_unit_id).first()
    if not unit:
        raise HTTPException(status_code=404, detail="Assigned storage unit not found")

    new_med = Medicine(
        storage_unit_id=med_in.storage_unit_id,
        medicine_name=med_in.medicine_name,
        generic_name=med_in.generic_name,
        category=med_in.category,
        required_min_temp=med_in.required_min_temp,
        required_max_temp=med_in.required_max_temp,
        required_min_humidity=med_in.required_min_humidity,
        required_max_humidity=med_in.required_max_humidity,
        light_sensitive=med_in.light_sensitive,
        storage_instructions=med_in.storage_instructions
    )
    db.add(new_med)
    db.commit()
    db.refresh(new_med)

    # Add batches if provided
    if med_in.batches:
        for b in med_in.batches:
            batch_record = MedicineBatch(
                medicine_id=new_med.id,
                batch_number=b.batch_number,
                quantity=b.quantity,
                manufacturing_date=b.manufacturing_date,
                expiry_date=b.expiry_date,
                supplier=b.supplier,
                current_status=b.current_status
            )
            db.add(batch_record)
        db.commit()
        db.refresh(new_med)

    AuditService.log_event(
        db, "MEDICINE_PROFILE_ADDED", "MEDICINE", new_med.id,
        details={"name": new_med.medicine_name, "unit": unit.unit_code}
    )
    return new_med

@router.get("/inventory/affected/{unit_id}", response_model=AffectedInventoryReport)
def get_affected_inventory(unit_id: int, db: Session = Depends(get_db)):
    unit = db.query(StorageUnit).filter(StorageUnit.id == unit_id).first()
    if not unit:
        raise HTTPException(status_code=404, detail="Storage unit not found")

    latest_reading = db.query(SensorReading).filter(
        SensorReading.storage_unit_id == unit.id
    ).order_by(SensorReading.timestamp.desc()).first()

    curr_temp = latest_reading.temperature if latest_reading else 4.0
    curr_humid = latest_reading.humidity if latest_reading else 50.0
    is_door_open = latest_reading.door_open if latest_reading else False
    lux = latest_reading.light_lux if latest_reading else 0.0

    medicines = db.query(Medicine).filter(Medicine.storage_unit_id == unit.id).all()
    
    affected_items: List[AffectedBatchItem] = []
    total_doses = 0

    for med in medicines:
        is_affected = False
        reasons = []

        # Check temperature deviation
        if curr_temp > med.required_max_temp:
            is_affected = True
            reasons.append(f"Temperature {curr_temp:.1f}°C exceeds allowed maximum ({med.required_max_temp:.1f}°C)")
        elif curr_temp < med.required_min_temp:
            is_affected = True
            reasons.append(f"Temperature {curr_temp:.1f}°C below freezing threshold ({med.required_min_temp:.1f}°C)")

        # Check light exposure for light-sensitive items
        if med.light_sensitive and (lux > 150.0 or is_door_open):
            is_affected = True
            reasons.append("Light-sensitive formulation exposed to elevated ambient light/open door")

        # Check humidity
        if curr_humid > med.required_max_humidity:
            is_affected = True
            reasons.append(f"Humidity {curr_humid:.1f}% exceeds max threshold ({med.required_max_humidity:.1f}%)")

        if is_affected:
            for b in med.batches:
                total_doses += b.quantity
                affected_items.append(AffectedBatchItem(
                    medicine_id=med.id,
                    medicine_name=med.medicine_name,
                    batch_id=b.id,
                    batch_number=b.batch_number,
                    quantity=b.quantity,
                    expiry_date=b.expiry_date,
                    required_min_temp=med.required_min_temp,
                    required_max_temp=med.required_max_temp,
                    light_sensitive=med.light_sensitive,
                    storage_instructions=med.storage_instructions,
                    deviation_description="; ".join(reasons)
                ))

    incident_active = len(affected_items) > 0 or unit.status in ["HIGH_RISK", "CRITICAL"]

    sop_guidance = (
        "STANDARD OPERATING PROCEDURE (SOP) ADVISORY:\n"
        "1. Quarantine affected storage compartment; do not discard stock automatically.\n"
        "2. Record elapsed excursion duration and peak temperature in the unit logbook.\n"
        "3. Consult product monograph / manufacturer stability data (e.g. WHO PQS / USP <1079>).\n"
        "4. Contact Quality Assurance Officer before returning stock to active dispensing."
    )

    return AffectedInventoryReport(
        storage_unit_id=unit.id,
        storage_unit_code=unit.unit_code,
        storage_unit_name=unit.name,
        current_temperature=curr_temp,
        current_humidity=curr_humid,
        current_risk_score=unit.current_risk_score,
        risk_level=unit.status,
        incident_active=incident_active,
        affected_batches_count=len(affected_items),
        total_doses_at_risk=total_doses,
        affected_items=affected_items,
        standard_operating_procedure=sop_guidance
    )
