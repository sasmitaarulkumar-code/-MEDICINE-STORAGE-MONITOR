from datetime import datetime, date
from typing import Optional, List
from pydantic import BaseModel, Field

class MedicineBatchCreate(BaseModel):
    batch_number: str = Field(..., example="BATCH-2026-X8")
    quantity: int = Field(default=50, ge=1)
    manufacturing_date: date = Field(default_factory=date.today)
    expiry_date: date
    supplier: str = "Serum Institute / Pfizer"
    current_status: str = "intact"

class MedicineBatchOut(BaseModel):
    id: int
    medicine_id: int
    batch_number: str
    quantity: int
    manufacturing_date: date
    expiry_date: date
    supplier: str
    current_status: str
    created_at: datetime

    class Config:
        from_attributes = True

class MedicineCreate(BaseModel):
    storage_unit_id: int
    medicine_name: str = Field(..., example="Insulin Glargine")
    generic_name: Optional[str] = "Insulin"
    category: str = "Biologics"
    required_min_temp: float = 2.0
    required_max_temp: float = 8.0
    required_min_humidity: float = 30.0
    required_max_humidity: float = 65.0
    light_sensitive: bool = True
    storage_instructions: Optional[str] = "Store between 2°C and 8°C. Do not freeze. Keep carton closed."
    batches: Optional[List[MedicineBatchCreate]] = None

class MedicineOut(BaseModel):
    id: int
    storage_unit_id: int
    medicine_name: str
    generic_name: Optional[str]
    category: str
    required_min_temp: float
    required_max_temp: float
    required_min_humidity: float
    required_max_humidity: float
    light_sensitive: bool
    storage_instructions: Optional[str]
    created_at: datetime
    batches: List[MedicineBatchOut] = []

    class Config:
        from_attributes = True

class AffectedBatchItem(BaseModel):
    medicine_id: int
    medicine_name: str
    batch_id: int
    batch_number: str
    quantity: int
    expiry_date: date
    required_min_temp: float
    required_max_temp: float
    light_sensitive: bool
    storage_instructions: Optional[str]
    deviation_description: str

class AffectedInventoryReport(BaseModel):
    storage_unit_id: int
    storage_unit_code: str
    storage_unit_name: str
    current_temperature: float
    current_humidity: float
    current_risk_score: float
    risk_level: str
    incident_active: bool
    affected_batches_count: int
    total_doses_at_risk: int
    affected_items: List[AffectedBatchItem]
    standard_operating_procedure: str
