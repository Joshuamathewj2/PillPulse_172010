from datetime import timedelta
from typing import List, Optional, Union

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, field_validator
from sqlalchemy.orm import Session

from app.core import clock
from app.database.db import get_db
from app.models.adherence_log import AdherenceLog
from app.models.medicine import Medicine

router = APIRouter(prefix="/medicines", tags=["medicines"])


def normalize_times(value: Union[str, List[str], None]) -> List[str]:
    items = value.split(",") if isinstance(value, str) else list(value or [])
    times = {t for t in (clock.to_24h(str(x)) for x in items) if t}
    return sorted(times)


class MedicineCreate(BaseModel):
    user_id: str
    medicine_name: str
    schedule_times: Union[str, List[str]] = ""
    dosage_per_day: Optional[int] = None
    total_pills: int = 0
    generic_name: Optional[str] = None
    dosage: Optional[str] = None
    instructions: Optional[str] = None
    duration_days: Optional[int] = None

    @field_validator("user_id", mode="before")
    @classmethod
    def _str_id(cls, v):
        return str(v)


class ConfirmDose(BaseModel):
    user_id: str
    medicine_id: int
    scheduled_time: str

    @field_validator("user_id", mode="before")
    @classmethod
    def _str_id(cls, v):
        return str(v)


def is_active(med: Medicine, day) -> bool:
    start = med.start_date or day
    if day < start:
        return False
    if med.duration_days:
        return day <= start + timedelta(days=med.duration_days - 1)
    return True


def serialize(med: Medicine) -> dict:
    return {
        "medicine_id": med.medicine_id,
        "user_id": med.user_id,
        "medicine_name": med.medicine_name,
        "generic_name": med.generic_name,
        "dosage": med.dosage,
        "dosage_per_day": med.dosage_per_day,
        "schedule_times": med.schedule_times,
        "instructions": med.instructions,
        "duration_days": med.duration_days,
        "start_date": med.start_date.isoformat() if med.start_date else None,
        "total_pills": med.total_pills,
        "remaining_pills": med.remaining_pills,
    }


@router.post("/add")
def add_medicine(medicine: MedicineCreate, db: Session = Depends(get_db)):
    times = normalize_times(medicine.schedule_times)
    per_day = medicine.dosage_per_day or max(len(times), 1)
    total = medicine.total_pills or (per_day * medicine.duration_days if medicine.duration_days else 0)

    # Re-scanning the same prescription should update, not duplicate.
    existing = (
        db.query(Medicine)
        .filter(Medicine.user_id == medicine.user_id, Medicine.medicine_name == medicine.medicine_name)
        .first()
    )
    med = existing or Medicine(user_id=medicine.user_id, medicine_name=medicine.medicine_name, start_date=clock.today())
    med.generic_name = medicine.generic_name
    med.dosage = medicine.dosage
    med.dosage_per_day = per_day
    med.schedule_times = ",".join(times)
    med.instructions = medicine.instructions
    med.duration_days = medicine.duration_days
    med.total_pills = total
    if not existing or existing.remaining_pills is None:
        med.remaining_pills = total
    if not existing:
        db.add(med)
    db.commit()
    db.refresh(med)
    return serialize(med)


@router.get("/list")
def list_medicines(user_id: str, db: Session = Depends(get_db)):
    return [serialize(m) for m in db.query(Medicine).filter(Medicine.user_id == user_id).all()]


@router.delete("/{medicine_id}")
def delete_medicine(medicine_id: int, user_id: str, db: Session = Depends(get_db)):
    med = db.query(Medicine).filter(Medicine.medicine_id == medicine_id, Medicine.user_id == user_id).first()
    if not med:
        raise HTTPException(status_code=404, detail="Medicine not found")
    db.delete(med)
    db.commit()
    return {"deleted": medicine_id}


def record_dose(db: Session, user_id: str, med: Medicine, scheduled_time: str) -> bool:
    """Log a taken dose once per (medicine, slot, day). Returns False if already logged."""
    today = clock.today()
    logs = db.query(AdherenceLog).filter(
        AdherenceLog.user_id == user_id,
        AdherenceLog.medicine_id == med.medicine_id,
        AdherenceLog.scheduled_time == scheduled_time,
        AdherenceLog.taken_status.is_(True),
    )
    if any(l.timestamp and l.timestamp.date() == today for l in logs):
        return False
    db.add(
        AdherenceLog(
            user_id=user_id,
            medicine_id=med.medicine_id,
            scheduled_time=scheduled_time,
            taken_status=True,
            timestamp=clock.now(),
        )
    )
    if med.remaining_pills and med.remaining_pills > 0:
        med.remaining_pills -= 1
    return True


@router.post("/confirm-dose")
def confirm_dose(dose: ConfirmDose, db: Session = Depends(get_db)):
    med = db.query(Medicine).filter(Medicine.medicine_id == dose.medicine_id, Medicine.user_id == dose.user_id).first()
    if not med:
        raise HTTPException(status_code=404, detail="Medicine not found")
    slot = clock.to_24h(dose.scheduled_time) or dose.scheduled_time
    created = record_dose(db, dose.user_id, med, slot)
    db.commit()
    return {"message": "Dose confirmed" if created else "Dose already recorded", "remaining_pills": med.remaining_pills}


@router.get("/today")
def get_today_medicines(user_id: str, db: Session = Depends(get_db)):
    today = clock.today()
    now_hm = clock.now().strftime("%H:%M")
    result = []
    for med in db.query(Medicine).filter(Medicine.user_id == user_id).all():
        if not is_active(med, today):
            continue
        taken_times = {
            log.scheduled_time
            for log in db.query(AdherenceLog).filter(
                AdherenceLog.medicine_id == med.medicine_id, AdherenceLog.user_id == user_id
            )
            if log.taken_status and log.timestamp and log.timestamp.date() == today
        }
        for stime in normalize_times(med.schedule_times):
            result.append(
                {
                    "medicine_id": med.medicine_id,
                    "medicine_name": med.medicine_name,
                    "dosage": med.dosage,
                    "instructions": med.instructions,
                    "scheduled_time": stime,
                    "taken": stime in taken_times,
                    "overdue": stime not in taken_times and stime < now_hm,
                }
            )
    return sorted(result, key=lambda r: r["scheduled_time"])


@router.get("/remaining")
def get_remaining(user_id: str, db: Session = Depends(get_db)):
    result = []
    for med in db.query(Medicine).filter(Medicine.user_id == user_id).all():
        per_day = med.dosage_per_day or 1
        days = (med.remaining_pills or 0) / per_day
        result.append(
            {
                "medicine_id": med.medicine_id,
                "medicine_name": med.medicine_name,
                "remaining_pills": med.remaining_pills,
                "remaining_days": round(days, 1),
                "refill_soon": med.total_pills > 0 and days <= 3,
            }
        )
    return result
