from datetime import datetime, date
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Date, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.database import Base

class Medicine(Base):
    __tablename__ = "medicines"

    id = Column(Integer, primary_key=True, index=True)
    storage_unit_id = Column(Integer, ForeignKey("storage_units.id"), nullable=False)
    medicine_name = Column(String(120), nullable=False, index=True)
    generic_name = Column(String(120), nullable=True)
    category = Column(String(80), default="Vaccine")  # Vaccine, Biologics, Insulin, Antibiotic, General
    
    # Specific temperature & storage requirements for this medicine
    required_min_temp = Column(Float, default=2.0)
    required_max_temp = Column(Float, default=8.0)
    required_min_humidity = Column(Float, default=30.0)
    required_max_humidity = Column(Float, default=65.0)
    light_sensitive = Column(Boolean, default=False)
    storage_instructions = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    storage_unit = relationship("StorageUnit", back_populates="medicines")
    batches = relationship("MedicineBatch", back_populates="medicine", cascade="all, delete-orphan")

class MedicineBatch(Base):
    __tablename__ = "medicine_batches"

    id = Column(Integer, primary_key=True, index=True)
    medicine_id = Column(Integer, ForeignKey("medicines.id"), nullable=False)
    batch_number = Column(String(60), unique=True, index=True, nullable=False)
    quantity = Column(Integer, default=100)
    manufacturing_date = Column(Date, default=date.today)
    expiry_date = Column(Date, nullable=False)
    supplier = Column(String(100), default="Serum Pharma Ltd")
    current_status = Column(String(30), default="intact")  # intact, under_investigation, quarantined
    created_at = Column(DateTime, default=datetime.utcnow)

    medicine = relationship("Medicine", back_populates="batches")
