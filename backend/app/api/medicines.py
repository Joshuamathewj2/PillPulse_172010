from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database.db import get_db
from app.models.medicine import Medicine
from app.models.adherence_log import AdherenceLog
from pydantic import BaseModel
from datetime import datetime, date

router = APIRouter(prefix="/medicines", tags=["medicines"])

class MedicineCreate(BaseModel):
    user_id: int
    medicine_name: str
    dosage_per_day: int
    schedule_times: str
    total_pills: int

class ConfirmDose(BaseModel):
    user_id: int
    medicine_id: int
    scheduled_time: str

@router.post("/add")
def add_medicine(medicine: MedicineCreate, db: Session = Depends(get_db)):
    new_med = Medicine(
        user_id=medicine.user_id,
        medicine_name=medicine.medicine_name,
        dosage_per_day=medicine.dosage_per_day,
        schedule_times=medicine.schedule_times,
        total_pills=medicine.total_pills,
        remaining_pills=medicine.total_pills
    )
    db.add(new_med)
    db.commit()
    db.refresh(new_med)
    return new_med

@router.post("/confirm-dose")
def confirm_dose(dose: ConfirmDose, db: Session = Depends(get_db)):
    # Create adherence log
    log = AdherenceLog(
        user_id=dose.user_id,
        medicine_id=dose.medicine_id,
        scheduled_time=dose.scheduled_time,
        taken_status=True
    )
    db.add(log)
    
    # Decrease remaining pills
    med = db.query(Medicine).filter(Medicine.medicine_id == dose.medicine_id).first()
    if med:
        if med.remaining_pills > 0:
            med.remaining_pills -= 1
    
    db.commit()
    return {"message": "Dose confirmed"}

@router.get("/today")
def get_today_medicines(user_id: int, db: Session = Depends(get_db)):
    # Returns the list of medicines for the user
    # Typically, daily schedule implies taking it every day.
    # So we just return all medicines for the user.
    meds = db.query(Medicine).filter(Medicine.user_id == user_id).all()
    
    # We could also join with AdherenceLog to see if taken today
    result = []
    today = date.today()
    for med in meds:
        logs = db.query(AdherenceLog).filter(
            AdherenceLog.medicine_id == med.medicine_id,
            AdherenceLog.user_id == user_id
        ).all()
        # filter logs for today
        taken_times = [log.scheduled_time for log in logs if log.timestamp.date() == today and log.taken_status]
        
        schedule_times = med.schedule_times.split(",") if med.schedule_times else []
        for stime in schedule_times:
            stime = stime.strip()
            if not stime:
                continue
            result.append({
                "medicine_id": med.medicine_id,
                "medicine_name": med.medicine_name,
                "scheduled_time": stime,
                "taken": stime in taken_times
            })
    return result

@router.get("/remaining")
def get_remaining(user_id: int, db: Session = Depends(get_db)):
    meds = db.query(Medicine).filter(Medicine.user_id == user_id).all()
    result = []
    for med in meds:
        remaining_days = 0
        if med.dosage_per_day > 0:
            remaining_days = med.remaining_pills / med.dosage_per_day
        result.append({
            "medicine_id": med.medicine_id,
            "medicine_name": med.medicine_name,
            "remaining_pills": med.remaining_pills,
            "remaining_days": remaining_days
        })
    return result
