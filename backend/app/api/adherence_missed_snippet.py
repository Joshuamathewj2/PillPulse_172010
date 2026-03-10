@router.get("/missed")
def get_missed_doses(user_id: int, db: Session = Depends(get_db)):
    # Calculate how many scheduled doses were missed.
    # A dose is considered "missed" if it's scheduled for a time that has passed today (or past days) and not marked as taken.
    # For MVP, let's simplify: Any adherence log with taken_status=False is a missed dose.
    # Actually, we don't create adherence_logs until they confirm it.
    # So a missed dose is when a scheduled dose doesn't have an adherence_log.
    
    meds = db.query(Medicine).filter(Medicine.user_id == user_id).all()
    today = date.today()
    missed_count = 0
    missed_details = []
    
    for med in meds:
        schedule_times = med.schedule_times.split(",") if med.schedule_times else []
        for stime in schedule_times:
            stime = stime.strip()
            if not stime: continue
            
            # check if there is a taken log for today
            log = db.query(AdherenceLog).filter(
                AdherenceLog.medicine_id == med.medicine_id,
                AdherenceLog.user_id == user_id,
                AdherenceLog.scheduled_time == stime,
                AdherenceLog.taken_status == True
            ).first()
            
            if not log:
                # If time has passed today
                now_str = datetime.now().strftime("%H:%M")
                if stime < now_str:
                    missed_count += 1
                    missed_details.append({"medicine_name": med.medicine_name, "scheduled_time": stime})
                    
    return {"missed_doses": missed_count, "details": missed_details}
