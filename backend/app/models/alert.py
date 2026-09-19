from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.database import Base

class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    storage_unit_id = Column(Integer, ForeignKey("storage_units.id"), nullable=False, index=True)
    alert_level = Column(String(20), default="WARNING")  # WARNING, HIGH_RISK, CRITICAL
    alert_type = Column(String(50), nullable=False)      # TEMP_HIGH, TEMP_LOW, HUMID_HIGH, DOOR_AJAR, POWER_FAIL, ANOMALY_SPIKE, TREND_WARNING
    trigger_value = Column(Float, nullable=False)
    allowed_range_min = Column(Float, nullable=True)
    allowed_range_max = Column(Float, nullable=True)
    duration_seconds = Column(Integer, default=0)
    status = Column(String(20), default="ACTIVE", index=True)  # ACTIVE, ACKNOWLEDGED, RESOLVED
    description = Column(String(255), nullable=False)
    recommended_action = Column(Text, nullable=False)
    triggered_at = Column(DateTime, default=datetime.utcnow, index=True)
    resolved_at = Column(DateTime, nullable=True)

    storage_unit = relationship("StorageUnit", back_populates="alerts")
    acknowledgements = relationship("AlertAcknowledgement", back_populates="alert", cascade="all, delete-orphan")

class AlertAcknowledgement(Base):
    __tablename__ = "alert_acknowledgements"

    id = Column(Integer, primary_key=True, index=True)
    alert_id = Column(Integer, ForeignKey("alerts.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    notes = Column(Text, nullable=False)
    acknowledged_at = Column(DateTime, default=datetime.utcnow)

    alert = relationship("Alert", back_populates="acknowledgements")
    user = relationship("User", back_populates="acknowledgements")
