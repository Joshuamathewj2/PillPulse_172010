from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.sql import func
from app.database.db import Base

class Patient(Base):
    __tablename__ = "patients"

    patient_code = Column(String, primary_key=True, index=True)  # "JOSH-4521"
    name = Column(String)
    fcm_token = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Caregiver(Base):
    __tablename__ = "caregivers"

    id = Column(Integer, primary_key=True, index=True)
    patient_code = Column(String, ForeignKey("patients.patient_code"), index=True)
    name = Column(String)
    relation = Column(String, nullable=True)
    fcm_token = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class DoseEvent(Base):
    """Every reminder outcome reported by the patient's device: taken, snoozed, skipped, escalated, missed."""

    __tablename__ = "dose_events"

    id = Column(Integer, primary_key=True, index=True)
    patient_code = Column(String, ForeignKey("patients.patient_code"), index=True)
    medicine_name = Column(String)
    timing_slot = Column(String)
    status = Column(String, index=True)
    client_timestamp = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
