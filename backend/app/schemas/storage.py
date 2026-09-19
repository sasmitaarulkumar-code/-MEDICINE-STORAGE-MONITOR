from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field

class StorageUnitCreate(BaseModel):
    unit_code: str = Field(..., example="UNIT-A-FRIDGE")
    name: str = Field(..., example="Pharmacy Refrigerator")
    unit_type: str = Field(default="refrigerator", example="refrigerator")
    location: str = Field(..., example="Room 102 - Ground Floor")
    default_min_temp: float = Field(default=2.0)
    default_max_temp: float = Field(default=8.0)
    default_min_humidity: float = Field(default=30.0)
    default_max_humidity: float = Field(default=65.0)

class StorageUnitUpdate(BaseModel):
    name: Optional[str] = None
    location: Optional[str] = None
    default_min_temp: Optional[float] = None
    default_max_temp: Optional[float] = None
    default_min_humidity: Optional[float] = None
    default_max_humidity: Optional[float] = None

class StorageUnitOut(BaseModel):
    id: int
    unit_code: str
    name: str
    unit_type: str
    location: str
    default_min_temp: float
    default_max_temp: float
    default_min_humidity: float
    default_max_humidity: float
    power_status: bool
    status: str
    current_risk_score: float
    door_open_state: bool
    last_ping: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True

class StorageUnitSummary(StorageUnitOut):
    latest_temperature: Optional[float] = None
    latest_humidity: Optional[float] = None
    latest_light_lux: Optional[float] = None
    active_alert_count: int = 0
    medicine_count: int = 0
    estimated_time_to_breach_min: Optional[float] = None
    trend_description: Optional[str] = None
