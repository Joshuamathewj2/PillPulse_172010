"""Patient / caregiver linking and dose-event escalation.

Ported from the old Flask app, where this state lived in an in-memory dict
that vanished on every restart. Paths and response shapes are unchanged so
existing clients keep working.
"""
from typing import Optional

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.medicines import record_dose
from app.core import clock
from app.database.db import get_db
from app.models.medicine import Medicine
from app.models.patient import Caregiver, DoseEvent, Patient
from app.services import fcm

router = APIRouter(prefix="/api", tags=["patients"])


class RegisterPatient(BaseModel):
    patientCode: str
    name: str
    token: Optional[str] = None


class RegisterCaregiver(BaseModel):
    patientCode: str
    caregiverName: str
    relation: Optional[str] = None
    token: Optional[str] = None


class LogDose(BaseModel):
    patientCode: str
    medicineName: str
    timingSlot: Optional[str] = ""
    status: str
    timestamp: Optional[str] = None


class NotifyCaregiver(BaseModel):
    patientCode: str
    medicineName: str
    timingSlot: Optional[str] = ""
    skipCount: Optional[int] = None


def _not_found():
    return JSONResponse(status_code=404, content={"success": False, "error": "Patient code not found"})


@router.post("/register-patient")
def register_patient(body: RegisterPatient, db: Session = Depends(get_db)):
    code = body.patientCode.strip().upper()
    patient = db.get(Patient, code) or Patient(patient_code=code)
    patient.name = body.name.strip()
    if body.token:
        patient.fcm_token = body.token
    db.merge(patient)
    db.commit()
    return {"success": True, "patientCode": code}


@router.post("/register-caregiver")
def register_caregiver(body: RegisterCaregiver, db: Session = Depends(get_db)):
    code = body.patientCode.strip().upper()
    patient = db.get(Patient, code)
    if not patient:
        return _not_found()
    db.add(Caregiver(patient_code=code, name=body.caregiverName, relation=body.relation, fcm_token=body.token))
    db.commit()
    fcm.send(body.token, "🏥 Connected to Patient", f"You are now monitoring {patient.name}.")
    return {"success": True, "patientName": patient.name}


@router.get("/patient-status")
def patient_status(patientCode: str, db: Session = Depends(get_db)):
    code = patientCode.strip().upper()
    patient = db.get(Patient, code)
    if not patient:
        return _not_found()
    events = (
        db.query(DoseEvent).filter(DoseEvent.patient_code == code).order_by(DoseEvent.id.desc()).limit(20).all()
    )
    caregivers = db.query(Caregiver).filter(Caregiver.patient_code == code).all()
    return {
        "success": True,
        "patientName": patient.name,
        # oldest -> newest, matching the original API
        "doseLog": [
            {
                "medicineName": e.medicine_name,
                "timingSlot": e.timing_slot,
                "status": e.status,
                "timestamp": e.client_timestamp or (e.created_at.isoformat() if e.created_at else None),
            }
            for e in reversed(events)
        ],
        "caregivers": [{"name": c.name, "relation": c.relation} for c in caregivers],
    }


@router.post("/log-dose")
def log_dose(body: LogDose, db: Session = Depends(get_db)):
    code = body.patientCode.strip().upper()
    if not db.get(Patient, code):
        return _not_found()
    db.add(
        DoseEvent(
            patient_code=code,
            medicine_name=body.medicineName,
            timing_slot=body.timingSlot,
            status=body.status,
            client_timestamp=body.timestamp,
        )
    )
    # A "taken" tap on a reminder counts toward adherence exactly like the dashboard button.
    if body.status == "taken":
        med = db.query(Medicine).filter(Medicine.user_id == code, Medicine.medicine_name == body.medicineName).first()
        slot = clock.to_24h(body.timingSlot or "")
        if med and slot:
            record_dose(db, code, med, slot)
    db.commit()
    return {"success": True}


@router.post("/notify-caregiver")
def notify_caregiver(body: NotifyCaregiver, db: Session = Depends(get_db)):
    code = body.patientCode.strip().upper()
    patient = db.get(Patient, code)
    if not patient:
        return _not_found()
    title = f"🚨 {patient.name} needs attention"
    text = f"{patient.name} has skipped their {body.medicineName} dose "
    text += f"{body.skipCount} times today ({body.timingSlot}). " if body.skipCount else f"at {body.timingSlot}. "
    text += "Please check on them."
    sent = 0
    for c in db.query(Caregiver).filter(Caregiver.patient_code == code).all():
        if fcm.send(c.fcm_token, title, text).get("success"):
            sent += 1
    caregiver_count = db.query(Caregiver).filter(Caregiver.patient_code == code).count()
    return {"success": True, "count": sent, "caregivers": caregiver_count, "push_configured": fcm.is_configured()}
