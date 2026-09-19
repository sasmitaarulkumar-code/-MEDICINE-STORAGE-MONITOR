from datetime import datetime
from sqlalchemy import Column, Integer, Float, Boolean, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from app.database import Base

class SensorReading(Base):
    __tablename__ = "sensor_readings"

    id = Column(Integer, primary_key=True, index=True)
    storage_unit_id = Column(Integer, ForeignKey("storage_units.id"), nullable=False, index=True)
    temperature = Column(Float, nullable=False)
    humidity = Column(Float, nullable=False)
    light_lux = Column(Float, default=0.0)
    door_open = Column(Boolean, default=False)
    power_connected = Column(Boolean, default=True)
    battery_level = Column(Float, default=3.3)
    is_offline_sync = Column(Boolean, default=False)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)

    storage_unit = relationship("StorageUnit", back_populates="readings")

# Index for fast time-series queries per storage unit
Index("idx_storage_unit_timestamp", SensorReading.storage_unit_id, SensorReading.timestamp)
