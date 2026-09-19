from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field

class TelemetryIngest(BaseModel):
    storage_unit_code: str
    temperature: float = Field(..., description="Storage temperature in °C")
    humidity: float = Field(..., description="Relative humidity in %")
    light_lux: float = Field(default=0.0, description="Ambient light in Lux")
    door_open: bool = Field(default=False, description="Door opened status")
    power_connected: bool = Field(default=True, description="Primary power status")
    battery_level: float = Field(default=3.3, description="Device battery voltage")
    is_offline_sync: bool = Field(default=False)
    timestamp: Optional[datetime] = None

class OfflineReadingItem(BaseModel):
    timestamp_offset_s: Optional[int] = None
    temperature: float
    humidity: float
    light_lux: float = 0.0
    door_open: bool = False
    power_connected: bool = True
    battery_level: float = 3.3
    timestamp: Optional[datetime] = None

class TelemetrySyncBatch(BaseModel):
    storage_unit_code: str
    readings: List[OfflineReadingItem]

class SensorReadingOut(BaseModel):
    id: int
    storage_unit_id: int
    temperature: float
    humidity: float
    light_lux: float
    door_open: bool
    power_connected: bool
    battery_level: float
    is_offline_sync: bool
    timestamp: datetime

    class Config:
        from_attributes = True
