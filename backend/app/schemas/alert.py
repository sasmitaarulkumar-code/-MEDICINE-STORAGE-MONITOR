from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field

class AlertAcknowledgementOut(BaseModel):
    id: int
    alert_id: int
    user_id: int
    user_name: Optional[str] = None
    notes: str
    acknowledged_at: datetime

    class Config:
        from_attributes = True

class AlertOut(BaseModel):
    id: int
    storage_unit_id: int
    storage_unit_name: Optional[str] = None
    alert_level: str
    alert_type: str
    trigger_value: float
    allowed_range_min: Optional[float] = None
    allowed_range_max: Optional[float] = None
    duration_seconds: int
    status: str
    description: str
    recommended_action: str
    triggered_at: datetime
    resolved_at: Optional[datetime] = None
    acknowledgements: List[AlertAcknowledgementOut] = []

    class Config:
        from_attributes = True

class AlertAcknowledgeRequest(BaseModel):
    notes: str = Field(..., min_length=3, example="Checked refrigerator door seal. Maintenance requested.")

class AlertResolveRequest(BaseModel):
    resolution_notes: str = Field(..., min_length=3, example="Re-calibrated sensor and closed door securely.")
