from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.alert import Alert, AlertAcknowledgement
from app.models.storage_unit import StorageUnit
from app.models.user import User
from app.schemas.alert import AlertOut, AlertAcknowledgeRequest, AlertResolveRequest
from app.services.audit_service import AuditService
from app.websocket_manager import ws_manager

router = APIRouter(prefix="/alerts", tags=["Alerts"])

@router.get("/active", response_model=List[AlertOut])
def get_active_alerts(db: Session = Depends(get_db)):
    alerts = db.query(Alert).filter(
        Alert.status.in_(["ACTIVE", "ACKNOWLEDGED"])
    ).order_by(Alert.triggered_at.desc()).all()
    
    results = []
    for a in alerts:
        results.append(AlertOut(
            id=a.id,
            storage_unit_id=a.storage_unit_id,
            storage_unit_name=a.storage_unit.name if a.storage_unit else "Unknown Unit",
            alert_level=a.alert_level,
            alert_type=a.alert_type,
            trigger_value=a.trigger_value,
            allowed_range_min=a.allowed_range_min,
            allowed_range_max=a.allowed_range_max,
            duration_seconds=a.duration_seconds,
            status=a.status,
            description=a.description,
            recommended_action=a.recommended_action,
            triggered_at=a.triggered_at,
            resolved_at=a.resolved_at,
            acknowledgements=[
                {
                    "id": ack.id,
                    "alert_id": ack.alert_id,
                    "user_id": ack.user_id,
                    "user_name": ack.user.full_name if ack.user else "Staff",
                    "notes": ack.notes,
                    "acknowledged_at": ack.acknowledged_at
                }
                for ack in a.acknowledgements
            ]
        ))
    return results

@router.get("/all", response_model=List[AlertOut])
def get_all_alerts(limit: int = 100, db: Session = Depends(get_db)):
    alerts = db.query(Alert).order_by(Alert.triggered_at.desc()).limit(limit).all()
    results = []
    for a in alerts:
        results.append(AlertOut(
            id=a.id,
            storage_unit_id=a.storage_unit_id,
            storage_unit_name=a.storage_unit.name if a.storage_unit else "Unknown Unit",
            alert_level=a.alert_level,
            alert_type=a.alert_type,
            trigger_value=a.trigger_value,
            allowed_range_min=a.allowed_range_min,
            allowed_range_max=a.allowed_range_max,
            duration_seconds=a.duration_seconds,
            status=a.status,
            description=a.description,
            recommended_action=a.recommended_action,
            triggered_at=a.triggered_at,
            resolved_at=a.resolved_at,
            acknowledgements=[
                {
                    "id": ack.id,
                    "alert_id": ack.alert_id,
                    "user_id": ack.user_id,
                    "user_name": ack.user.full_name if ack.user else "Staff",
                    "notes": ack.notes,
                    "acknowledged_at": ack.acknowledged_at
                }
                for ack in a.acknowledgements
            ]
        ))
    return results

@router.post("/{id}/acknowledge")
async def acknowledge_alert(
    id: int,
    req: AlertAcknowledgeRequest,
    db: Session = Depends(get_db)
):
    alert = db.query(Alert).filter(Alert.id == id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    # Find a default staff user if no user logged in
    user = db.query(User).first()
    user_id = user.id if user else 1

    ack = AlertAcknowledgement(
        alert_id=alert.id,
        user_id=user_id,
        notes=req.notes,
        acknowledged_at=datetime.utcnow()
    )
    db.add(ack)
    alert.status = "ACKNOWLEDGED"
    db.commit()

    AuditService.log_event(
        db, "ALERT_ACKNOWLEDGED", "ALERT", alert.id, user_id=user_id,
        details={"notes": req.notes, "alert_type": alert.alert_type}
    )

    await ws_manager.broadcast({
        "event_type": "ALERT_ACKNOWLEDGED",
        "alert_id": alert.id,
        "notes": req.notes,
        "status": "ACKNOWLEDGED"
    })

    return {"message": "Alert acknowledged successfully", "status": "ACKNOWLEDGED"}

@router.post("/{id}/resolve")
async def resolve_alert(
    id: int,
    req: AlertResolveRequest,
    db: Session = Depends(get_db)
):
    alert = db.query(Alert).filter(Alert.id == id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    alert.status = "RESOLVED"
    alert.resolved_at = datetime.utcnow()
    db.commit()

    AuditService.log_event(
        db, "ALERT_RESOLVED_MANUAL", "ALERT", alert.id,
        details={"resolution_notes": req.resolution_notes, "alert_type": alert.alert_type}
    )

    await ws_manager.broadcast({
        "event_type": "ALERT_RESOLVED",
        "alert_id": alert.id,
        "status": "RESOLVED"
    })

    return {"message": "Alert marked as resolved", "status": "RESOLVED"}
