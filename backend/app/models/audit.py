from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.database import Base

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # Nullable for background system actions
    action = Column(String(80), nullable=False, index=True)           # THRESHOLD_UPDATE, ALERT_ACKNOWLEDGE, OFFLINE_SYNC, POWER_EVENT
    entity_type = Column(String(50), nullable=False)                  # STORAGE_UNIT, ALERT, MEDICINE, SENSOR
    entity_id = Column(Integer, nullable=True)
    details_json = Column(Text, nullable=True)
    ip_address = Column(String(45), default="127.0.0.1")
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)

    user = relationship("User", back_populates="audit_logs")
