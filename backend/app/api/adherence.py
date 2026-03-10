from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database.db import get_db
from app.models.adherence_log import AdherenceLog

router = APIRouter(prefix="/adherence", tags=["adherence"])

@router.get("/score")
def get_adherence_score(user_id: int, db: Session = Depends(get_db)):
    logs = db.query(AdherenceLog).filter(AdherenceLog.user_id == user_id).all()
    if not logs:
        return {"score": 100.0}

    total_doses = len(logs)
    taken_doses = sum(1 for log in logs if log.taken_status)
    
    score = (taken_doses / total_doses) * 100 if total_doses > 0 else 100.0
    return {"score": score}

@router.get("/missed")
def get_missed_doses(user_id: int, db: Session = Depends(get_db)):
    from app.models.medicine import Medicine
    from datetime import datetime, date
    
    meds = db.query(Medicine).filter(Medicine.user_id == user_id).all()
    today = date.today()
    missed_count = 0
    missed_details = []
    
    for med in meds:
        schedule_times = med.schedule_times.split(",") if med.schedule_times else []
        for stime in schedule_times:
            stime = stime.strip()
            if not stime: continue
            
            from sqlalchemy import and_
            log = db.query(AdherenceLog).filter(
                and_(
                    AdherenceLog.medicine_id == med.medicine_id,
                    AdherenceLog.user_id == user_id,
                    AdherenceLog.scheduled_time == stime,
                    AdherenceLog.taken_status == True
                )
            ).first()
            
            if not log:
                now_str = datetime.now().strftime("%H:%M")
                if stime < now_str:
                    missed_count += 1
                    missed_details.append({"medicine_name": med.medicine_name, "scheduled_time": stime})
                    
    return {"missed_doses": missed_count, "details": missed_details}
