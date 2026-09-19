from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.database import Base

class StorageUnit(Base):
    __tablename__ = "storage_units"

    id = Column(Integer, primary_key=True, index=True)
    unit_code = Column(String(50), unique=True, index=True, nullable=False)
    name = Column(String(100), nullable=False)
    unit_type = Column(String(50), default="refrigerator")  # refrigerator, vaccine_freezer, ambient_cabinet
    location = Column(String(150), nullable=False)
    
    # Configurable limits
    default_min_temp = Column(Float, default=2.0)
    default_max_temp = Column(Float, default=8.0)
    default_min_humidity = Column(Float, default=30.0)
    default_max_humidity = Column(Float, default=65.0)
    
    # Live operational status
    power_status = Column(Boolean, default=True)  # True = Healthy Mains Power
    status = Column(String(20), default="SAFE")    # SAFE, CAUTION, HIGH_RISK, CRITICAL
    current_risk_score = Column(Float, default=0.0)
    door_open_state = Column(Boolean, default=False)
    last_ping = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    readings = relationship("SensorReading", back_populates="storage_unit", cascade="all, delete-orphan")
    medicines = relationship("Medicine", back_populates="storage_unit")
    alerts = relationship("Alert", back_populates="storage_unit", cascade="all, delete-orphan")
    incidents = relationship("Incident", back_populates="storage_unit")
    maintenance_events = relationship("MaintenanceEvent", back_populates="storage_unit")

class MaintenanceEvent(Base):
    __tablename__ = "maintenance_events"

    id = Column(Integer, primary_key=True, index=True)
    storage_unit_id = Column(Integer, ForeignKey("storage_units.id"), nullable=False)
    event_type = Column(String(50), nullable=False)  # calibration, compressor_service, sensor_replacement
    description = Column(Text, nullable=False)
    technician_name = Column(String(100), nullable=False)
    event_date = Column(DateTime, default=datetime.utcnow)
    next_scheduled_date = Column(DateTime, nullable=True)

    storage_unit = relationship("StorageUnit", back_populates="maintenance_events")

class Incident(Base):
    __tablename__ = "incidents"

    id = Column(Integer, primary_key=True, index=True)
    storage_unit_id = Column(Integer, ForeignKey("storage_units.id"), nullable=False)
    incident_code = Column(String(50), unique=True, index=True, nullable=False)
    severity = Column(String(20), default="MEDIUM")  # LOW, MEDIUM, HIGH, CRITICAL
    start_time = Column(DateTime, default=datetime.utcnow)
    end_time = Column(DateTime, nullable=True)
    peak_temperature = Column(Float, nullable=True)
    total_duration_minutes = Column(Integer, default=0)
    root_cause = Column(Text, nullable=True)
    corrective_action_summary = Column(Text, nullable=True)
    final_status = Column(String(20), default="OPEN")  # OPEN, UNDER_REVIEW, CLOSED

    storage_unit = relationship("StorageUnit", back_populates="incidents")
